"""
Main CLI entry point for the Algorzen Data Quality Toolkit.

This module provides the command-line interface for the data quality toolkit,
allowing users to run quality checks, generate reports, and manage configurations.
"""

import asyncio
import click
import pandas as pd
from pathlib import Path
from typing import Optional
import json
import subprocess
import sys
import webbrowser
import time
import os
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

from ..core.engine import DataQualityEngine
from ..utils.logging import setup_logging, get_logger

console = Console()

logger = get_logger(__name__)


def print_banner():
    """Prints a fancy banner for the CLI."""
    banner = """
  _   _      _ _         __        __         _     _ _ 
 | | | |    | | |        \ \      / /        | |   | | |
 | |_| | ___| | | ___     \ \ /\ / /__  _ __ | | __| | |
 |  _  |/ _ \ | |/ _ \     \ /  \ / _ \| '_ \| |/ _` | |
 | | | |  __/ | | (_) |     \  /\  / (_) | | | | | (_| |_|
 |_| |_|\___|_|_|\___( )     \/  \/ \___/|_| |_|_|\__,_(_)
                      |/                                  
"""
    console.print(Panel(Text(banner, justify="center"), title="Algorzen Data Quality Toolkit", border_style="blue"))


def print_feature_tree():
    """Prints a feature tree for the CLI."""
    features = """
[bold green]*[/bold green] [bold]API Server[/bold] - FastAPI backend for React frontend
[bold green]*[/bold green] [bold]Quality Checks[/bold] - Run comprehensive data validation rules
[bold green]*[/bold green] [bold]Data Profiling[/bold] - Analyze data structure and patterns
[bold green]*[/bold green] [bold]Reports[/bold] - Generate detailed HTML, JSON, or CSV reports
[bold green]*[/bold green] [bold]Configuration Management[/bold] - Manage quality check rules and thresholds
[bold green]*[/bold green] [bold]Monitoring Stack[/bold] - Full Prometheus + Grafana monitoring
"""
    console.print(Panel(Text(features, justify="center"), title="Features", border_style="green"))


def print_success(message: str):
    """Prints a success message with a checkmark."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str):
    """Prints an error message with a cross."""
    console.print(f"[bold red]❌[/bold red] {message}")


def animate_loading(message: str, duration: float):
    """Animates a loading spinner for a given duration."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(message, total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            time.sleep(duration / 100)


@click.group()
@click.option('--log-level', default='INFO', help='Logging level')
@click.option('--log-file', help='Log file path')
@click.option('--config', help='Configuration file path')
@click.pass_context
def cli(ctx, log_level: str, log_file: Optional[str], config: Optional[str]):
    """
    Algorzen Data Quality Toolkit - Enterprise-grade data validation and quality monitoring.
    
    This toolkit provides comprehensive data quality checks, validation rules,
    and reporting capabilities for various data sources and formats.
    """
    # Setup logging
    setup_logging(level=log_level, log_file=Path(log_file) if log_file else None)
    
    # Store context
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['log_level'] = log_level
    
    # Print banner and features
    print_banner()
    print_feature_tree()
    
    logger.info("Algorzen Data Quality Toolkit CLI started")


@cli.command()
@click.argument('data_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output report path')
@click.option('--format', 'report_format', default='html', 
              type=click.Choice(['html', 'json', 'csv']), help='Report format')
@click.option('--checks', help='Comma-separated list of check types to run')
@click.option('--config', help='Quality check configuration file')
@click.pass_context
def check(ctx, data_path: str, output: Optional[str], report_format: str, 
          checks: Optional[str], config: Optional[str]):
    """
    Run data quality checks on a dataset.
    
    DATA_PATH: Path to the data file (CSV, JSON, Excel, etc.)
    """
    console.print(f"\n🔍 [bold cyan]Starting Quality Checks[/bold cyan]")
    console.print(f"📁 Data file: [yellow]{data_path}[/yellow]")
    
    animate_loading("Initializing Data Quality Engine...", 1.5)
    
    async def run_checks():
        # Initialize engine
        engine = DataQualityEngine(
            config_path=config or ctx.obj.get('config'),
            enable_monitoring=True
        )
        
        try:
            # Load data
            console.print("📊 Loading data...")
            animate_loading("Loading and analyzing data...", 1.0)
            data = pd.read_csv(data_path)  # TODO: Support multiple formats
            
            # Parse check types
            check_types = None
            if checks:
                check_types = [c.strip() for c in checks.split(',')]
                console.print(f"🎯 Running checks: [green]{', '.join(check_types)}[/green]")
            else:
                console.print("🎯 Running all available quality checks...")
            
            # Run quality checks
            console.print("⚡ Executing quality checks...")
            animate_loading("Running quality checks...", 2.0)
            results = await engine.run_quality_checks(data, check_types)
            
            # Display summary
            summary = engine.get_summary()
            
            # Create fancy summary table
            summary_table = Table(title="🎯 [bold green]Quality Check Summary[/bold green]", box=box.ROUNDED)
            summary_table.add_column("Metric", style="cyan", no_wrap=True)
            summary_table.add_column("Value", style="green")
            
            summary_table.add_row("📊 Total Checks", str(summary['total_checks']))
            summary_table.add_row("✅ Passed", str(summary['passed']))
            summary_table.add_row("❌ Failed", str(summary['failed']))
            summary_table.add_row("⚠️ Warnings", str(summary['warnings']))
            summary_table.add_row("🎯 Overall Score", f"{summary['overall_score']:.2%}")
            summary_table.add_row("⏱️ Execution Time", f"{summary['execution_time']:.2f}s")
            
            console.print(summary_table)
            
            # Generate report if requested
            if output:
                console.print(f"📄 Generating {report_format} report...")
                animate_loading("Generating report...", 1.5)
                report_path = await engine.generate_report(
                    report_type=report_format,
                    output_path=output
                )
                print_success(f"Report saved to: {report_path}")
            
            # Display detailed results
            if results:
                console.print("\n📋 [bold cyan]Detailed Results[/bold cyan]")
                
                results_table = Table(box=box.ROUNDED)
                results_table.add_column("Status", style="white", no_wrap=True)
                results_table.add_column("Check Name", style="cyan")
                results_table.add_column("Type", style="yellow")
                results_table.add_column("Score", style="green")
                results_table.add_column("Time", style="magenta")
                
                for result in results:
                    status_icon = {
                        'passed': '✅',
                        'failed': '❌',
                        'warning': '⚠️',
                        'error': '💥'
                    }.get(result.status, '❓')
                    
                    results_table.add_row(
                        status_icon,
                        result.check_name,
                        result.check_type,
                        f"{result.score:.2%}",
                        f"{result.execution_time:.3f}s"
                    )
                
                console.print(results_table)
            
        except Exception as e:
            print_error(f"Error during quality checks: {e}")
            logger.error(f"Error during quality checks: {e}")
            raise click.Abort()
        
        finally:
            await engine.cleanup()
    
    # Run async function
    asyncio.run(run_checks())


@cli.command()
@click.argument('data_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def profile(ctx, data_path: str, output: Optional[str]):
    """
    Generate a data profile report.
    
    DATA_PATH: Path to the data file to profile
    """
    console.print(f"\n📊 [bold cyan]Generating Data Profile[/bold cyan]")
    console.print(f"📁 Data file: [yellow]{data_path}[/yellow]")
    
    try:
        # Load data
        animate_loading("Loading data for profiling...", 1.5)
        data = pd.read_csv(data_path)
        
        # Basic profiling
        console.print("🔍 Analyzing data structure...")
        animate_loading("Analyzing data structure and patterns...", 2.0)
        
        profile_info = {
            "file_path": data_path,
            "shape": data.shape,
            "columns": list(data.columns),
            "data_types": data.dtypes.to_dict(),
            "missing_values": data.isnull().sum().to_dict(),
            "memory_usage": data.memory_usage(deep=True).sum(),
            "numeric_columns": data.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": data.select_dtypes(include=['object']).columns.tolist(),
            "date_columns": data.select_dtypes(include=['datetime']).columns.tolist()
        }
        
        # Display profile
        profile_table = Table(title="📊 [bold green]Data Profile Summary[/bold green]", box=box.ROUNDED)
        profile_table.add_column("Metric", style="cyan", no_wrap=True)
        profile_table.add_column("Value", style="green")
        
        profile_table.add_row("📁 File Path", profile_info['file_path'])
        profile_table.add_row("📊 Shape", f"{profile_info['shape'][0]} rows × {profile_info['shape'][1]} columns")
        profile_table.add_row("💾 Memory Usage", f"{profile_info['memory_usage'] / 1024:.2f} KB")
        profile_table.add_row("🔢 Numeric Columns", str(len(profile_info['numeric_columns'])))
        profile_table.add_row("📝 Categorical Columns", str(len(profile_info['categorical_columns'])))
        profile_table.add_row("📅 Date Columns", str(len(profile_info['date_columns'])))
        
        console.print(profile_table)
        
        # Missing values analysis
        if any(profile_info['missing_values'].values()):
            console.print("\n⚠️ [bold yellow]Missing Values Analysis[/bold yellow]")
            
            missing_table = Table(box=box.ROUNDED)
            missing_table.add_column("Column", style="cyan")
            missing_table.add_column("Missing Count", style="red")
            missing_table.add_column("Percentage", style="yellow")
            
            for col, missing in profile_info['missing_values'].items():
                if missing > 0:
                    percentage = (missing / profile_info['shape'][0]) * 100
                    missing_table.add_row(col, str(missing), f"{percentage:.1f}%")
            
            console.print(missing_table)
        
        # Save profile if requested
        if output:
            animate_loading("Saving profile to file...", 1.0)
            with open(output, 'w') as f:
                json.dump(profile_info, f, indent=2, default=str)
            print_success(f"Profile saved to: {output}")
    
    except Exception as e:
        print_error(f"Error during data profiling: {e}")
        logger.error(f"Error during data profiling: {e}")
        raise click.Abort()


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--open-browser', is_flag=True, help='Automatically open browser')
@click.pass_context
def api_server(ctx, host: str, port: int, open_browser: bool):
    """
    Launch the API server for the React frontend.
    
    This command starts the FastAPI server with all the API endpoints
    needed by the React dashboard.
    """
    logger.info(f"Starting API server on {host}:{port}")
    
    try:
        # Import API server
        from ..api.server import app
        
        # Start the API server
        console.print(f"🚀 Starting Algorzen Data Quality API Server...")
        console.print(f"📍 API Server URL: http://{host}:{port}")
        console.print(f"📊 API Documentation: http://{host}:{port}/docs")
        console.print(f"🔧 Health Check: http://{host}:{port}/health")
        console.print(f"🌐 React Dashboard: Use 'cd frontend/algorzen-dashboard && npm start'")
        console.print("\nPress Ctrl+C to stop the API server")
        
        # Open browser if requested
        if open_browser:
            time.sleep(2)  # Wait for server to start
            webbrowser.open(f"http://{host}:{port}/docs")
        
        # Start the server
        import uvicorn
        uvicorn.run(app, host=host, port=port)
        
    except ImportError as e:
        print_error(f"❌ Error: Failed to import API server: {e}")
        console.print("Make sure all dependencies are installed: pip install -e .")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error starting API server: {e}")
        print_error(f"❌ Error: {e}")
        raise click.Abort()


@cli.command()
@click.option('--config', help='Configuration file path')
@click.pass_context
def validate(ctx, config: Optional[str]):
    """
    Validate configuration and system requirements.
    """
    logger.info("Validating system configuration")
    
    try:
        # Check Python version
        import sys
        python_version = sys.version_info
        console.print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check required packages
        required_packages = [
            'pandas', 'numpy', 'fastapi', 'pydantic', 'click', 'rich'
        ]
        
        console.print("\nChecking required packages:")
        for package in required_packages:
            try:
                __import__(package)
                console.print(f"  ✅ {package}")
            except ImportError:
                console.print(f"  ❌ {package} (not installed)")
        
        # Check configuration
        if config:
            config_path = Path(config)
            if config_path.exists():
                console.print(f"\n✅ Configuration file found: {config}")
            else:
                console.print(f"\n❌ Configuration file not found: {config}")
        
        # Check data directory
        data_dir = Path.cwd()
        if data_dir.exists():
            console.print(f"\n✅ Working directory: {data_dir}")
        else:
            console.print(f"\n❌ Working directory not accessible: {data_dir}")
        
        console.print("\n✅ System validation completed")
    
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        print_error(f"❌ Validation error: {e}")
        raise click.Abort()


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    from .. import __version__, __author__
    
    console.print(f"Algorzen Data Quality Toolkit v{__version__}")
    console.print(f"Author: {__author__}")
    console.print("Enterprise-grade data validation and quality monitoring")


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=3000, help='Port to bind to')
@click.option('--open-browser', is_flag=True, help='Automatically open browser')
@click.pass_context
def grafana(ctx, host: str, port: int, open_browser: bool):
    """
    Launch Grafana monitoring dashboard.
    
    This command starts Grafana for data quality metrics visualization.
    """
    logger.info(f"Starting Grafana on {host}:{port}")
    
    try:
        console.print(f"📊 Starting Grafana Dashboard...")
        console.print(f"📍 Grafana URL: http://{host}:{port}")
        console.print(f"👤 Default credentials: admin/admin")
        console.print(f"🔗 Algorzen DQT Dashboard: http://{host}:{port}/d/algorzen-dqt-overview")
        console.print("\nPress Ctrl+C to stop Grafana")
        
        # Open browser if requested
        if open_browser:
            time.sleep(2)
            webbrowser.open(f"http://{host}:{port}")
        
        # Start Grafana using docker-compose
        import subprocess
        subprocess.run([
            "docker-compose", "up", "-d", "grafana"
        ], check=True)
        
        console.print("✅ Grafana started successfully!")
        console.print("Use 'docker-compose logs grafana' to view logs")
        console.print("Use 'docker-compose stop grafana' to stop")
        
    except subprocess.CalledProcessError as e:
        print_error(f"❌ Error starting Grafana: {e}")
        console.print("Make sure Docker and docker-compose are installed and running")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error starting Grafana: {e}")
        print_error(f"❌ Error: {e}")
        raise click.Abort()


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=9090, help='Port to bind to')
@click.option('--open-browser', is_flag=True, help='Automatically open browser')
@click.pass_context
def prometheus(ctx, host: str, port: int, open_browser: bool):
    """
    Launch Prometheus metrics server.
    
    This command starts Prometheus for collecting data quality metrics.
    """
    logger.info(f"Starting Prometheus on {host}:{port}")
    
    try:
        console.print(f"📈 Starting Prometheus Metrics Server...")
        console.print(f"📍 Prometheus URL: http://{host}:{port}")
        console.print(f"📊 Metrics Endpoint: http://{host}:{port}/metrics")
        console.print(f"🎯 Targets: http://{host}:{port}/targets")
        console.print("\nPress Ctrl+C to stop Prometheus")
        
        # Open browser if requested
        if open_browser:
            time.sleep(2)
            webbrowser.open(f"http://{host}:{port}")
        
        # Start Prometheus using docker-compose
        import subprocess
        subprocess.run([
            "docker-compose", "up", "-d", "prometheus"
        ], check=True)
        
        console.print("✅ Prometheus started successfully!")
        console.print("Use 'docker-compose logs prometheus' to view logs")
        console.print("Use 'docker-compose stop prometheus' to stop")
        
    except subprocess.CalledProcessError as e:
        print_error(f"❌ Error starting Prometheus: {e}")
        console.print("Make sure Docker and docker-compose are installed and running")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error starting Prometheus: {e}")
        print_error(f"❌ Error: {e}")
        raise click.Abort()


@cli.command()
@click.pass_context
def monitoring(ctx):
    """
    Launch complete monitoring stack (Prometheus + Grafana).
    
    This command starts the full monitoring infrastructure for data quality.
    """
    logger.info("Starting complete monitoring stack")
    
    try:
        console.print(f"🚀 Starting Complete Monitoring Stack...")
        console.print(f"📊 Prometheus: http://127.0.0.1:9090")
        console.print(f"📈 Grafana: http://127.0.0.1:3000")
        console.print(f"🔗 Algorzen DQT Dashboard: http://127.0.0.1:3000/d/algorzen-dqt-overview")
        console.print("\nStarting services...")
        
        # Start monitoring stack using docker-compose
        import subprocess
        
        # Start Prometheus and Grafana
        subprocess.run([
            "docker-compose", "up", "-d", "prometheus", "grafana"
        ], check=True)
        
        console.print("✅ Monitoring stack started successfully!")
        console.print("\n📋 Quick Commands:")
        console.print("  View logs: docker-compose logs -f")
        console.print("  Stop all: docker-compose stop")
        console.print("  Restart: docker-compose restart")
        console.print("  Status: docker-compose ps")
        
        console.print("\n🌐 Access URLs:")
        console.print("  Prometheus: http://127.0.0.1:9090")
        console.print("  Grafana: http://127.0.0.1:3000 (admin/admin)")
        
    except subprocess.CalledProcessError as e:
        print_error(f"❌ Error starting monitoring stack: {e}")
        console.print("Make sure Docker and docker-compose are installed and running")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error starting monitoring stack: {e}")
        print_error(f"❌ Error: {e}")
        raise click.Abort()


@cli.command()
@click.option('--service', help='Specific service to check (prometheus, grafana, all)')
@click.pass_context
def status(ctx, service: Optional[str]):
    """
    Check status of monitoring services.
    """
    logger.info("Checking monitoring services status")
    
    try:
        import subprocess
        
        if service and service not in ['prometheus', 'grafana', 'all']:
            print_error(f"❌ Invalid service: {service}. Use: prometheus, grafana, or all")
            return
        
        # Check Docker services
        result = subprocess.run([
            "docker-compose", "ps"
        ], capture_output=True, text=True, check=True)
        
        console.print("📊 Monitoring Services Status:")
        console.print("=" * 50)
        
        if service == 'prometheus' or service == 'all' or not service:
            console.print("\n🔍 Prometheus:")
            if 'prometheus' in result.stdout:
                console.print("  ✅ Running")
            else:
                console.print("  ❌ Not running")
        
        if service == 'grafana' or service == 'all' or not service:
            console.print("\n📈 Grafana:")
            if 'grafana' in result.stdout:
                console.print("  ✅ Running")
            else:
                console.print("  ❌ Not running")
        
        if not service:
            console.print("\n📋 All Services:")
            console.print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print_error(f"❌ Error checking status: {e}")
        console.print("Make sure Docker and docker-compose are installed and running")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        print_error(f"❌ Error: {e}")
        raise click.Abort()


@cli.command()
@click.option('--service', help='Specific service to restart (prometheus, grafana, all)')
@click.pass_context
def restart(ctx, service: Optional[str]):
    """
    Restart monitoring services.
    """
    logger.info(f"Restarting monitoring services: {service or 'all'}")
    
    try:
        import subprocess
        
        if service and service not in ['prometheus', 'grafana', 'all']:
            print_error(f"❌ Invalid service: {service}. Use: prometheus, grafana, or all")
            return
        
        if service == 'all' or not service:
            console.print("🔄 Restarting all monitoring services...")
            subprocess.run([
                "docker-compose", "restart", "prometheus", "grafana"
            ], check=True)
            console.print("✅ All services restarted successfully!")
        else:
            console.print(f"🔄 Restarting {service}...")
            subprocess.run([
                "docker-compose", "restart", service
            ], check=True)
            console.print(f"✅ {service} restarted successfully!")
        
    except subprocess.CalledProcessError as e:
        print_error(f"❌ Error restarting services: {e}")
        console.print("Make sure Docker and docker-compose are installed and running")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error restarting services: {e}")
        print_error(f"❌ Error: {e}")
        raise click.Abort()


@cli.command()
@click.option('--service', help='Specific service to stop (prometheus, grafana, all)')
@click.pass_context
def stop(ctx, service: Optional[str]):
    """
    Stop monitoring services.
    """
    logger.info(f"Stopping monitoring services: {service or 'all'}")
    
    try:
        import subprocess
        
        if service and service not in ['prometheus', 'grafana', 'all']:
            print_error(f"❌ Invalid service: {service}. Use: prometheus, grafana, or all")
            return
        
        if service == 'all' or not service:
            console.print("🛑 Stopping all monitoring services...")
            subprocess.run([
                "docker-compose", "stop", "prometheus", "grafana"
            ], check=True)
            console.print("✅ All services stopped successfully!")
        else:
            console.print(f"🛑 Stopping {service}...")
            subprocess.run([
                "docker-compose", "stop", service
            ], check=True)
            console.print(f"✅ {service} stopped successfully!")
        
    except subprocess.CalledProcessError as e:
        print_error(f"❌ Error stopping services: {e}")
        console.print("Make sure Docker and docker-compose are installed and running")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error stopping services: {e}")
        print_error(f"❌ Error: {e}")
        raise click.Abort()


@cli.command()
@click.option('--url', default='http://127.0.0.1:3000', help='Grafana URL')
@click.option('--username', default='admin', help='Grafana username')
@click.option('--password', default='admin', help='Grafana password')
@click.pass_context
def setup_grafana(ctx, url: str, username: str, password: str):
    """
    Setup Grafana with Algorzen DQT dashboards and datasources.
    """
    logger.info(f"Setting up Grafana at {url}")
    
    try:
        console.print(f"�� Setting up Grafana at {url}")
        console.print(f"👤 Using credentials: {username}/{password}")
        
        # Check if Grafana is running
        import requests
        import time
        
        # Wait for Grafana to be ready
        console.print("⏳ Waiting for Grafana to be ready...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f"{url}/api/health", timeout=5)
                if response.status_code == 200:
                    console.print("✅ Grafana is ready!")
                    break
            except requests.RequestException:
                if i == 29:
                    print_error("❌ Grafana is not responding. Make sure it's running.")
                    return
                time.sleep(1)
                console.print(f"⏳ Waiting... ({i+1}/30)")
        
        # Import dashboard
        console.print("📊 Importing Algorzen DQT Dashboard...")
        
        # This would typically use Grafana API to import dashboards
        # For now, provide instructions
        console.print("\n📋 Manual Setup Instructions:")
        console.print("1. Go to Grafana: " + url)
        console.print("2. Login with: " + username + "/" + password)
        console.print("3. Go to + > Import")
        console.print("4. Upload: monitoring/grafana/dashboards/algorzen-dqt-dashboard.json")
        console.print("5. Select Prometheus as datasource")
        console.print("6. Click Import")
        
        console.print("\n✅ Grafana setup instructions provided!")
        
    except ImportError:
        print_error("❌ Error: requests library not installed")
        console.print("Install with: pip install requests")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error setting up Grafana: {e}")
        print_error(f"❌ Error: {e}")
        raise click.Abort()


@cli.command()
@click.option('--url', default='http://127.0.0.1:9090', help='Prometheus URL')
@click.pass_context
def setup_prometheus(ctx, url: str):
    """
    Setup Prometheus for Algorzen DQT metrics collection.
    """
    logger.info(f"Setting up Prometheus at {url}")
    
    try:
        console.print(f"🔧 Setting up Prometheus at {url}")
        
        # Check if Prometheus is running
        import requests
        import time
        
        # Wait for Prometheus to be ready
        console.print("⏳ Waiting for Prometheus to be ready...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f"{url}/-/ready", timeout=5)
                if response.status_code == 200:
                    console.print("✅ Prometheus is ready!")
                    break
            except requests.RequestException:
                if i == 29:
                    print_error("❌ Prometheus is not responding. Make sure it's running.")
                    return
                time.sleep(1)
                console.print(f"⏳ Waiting... ({i+1}/30)")
        
        # Check targets
        console.print("🎯 Checking Prometheus targets...")
        try:
            response = requests.get(f"{url}/api/v1/targets", timeout=5)
            if response.status_code == 200:
                targets = response.json()
                active_targets = [t for t in targets.get('data', {}).get('activeTargets', []) if t.get('health') == 'up']
                console.print(f"✅ Found {len(active_targets)} active targets")
            else:
                console.print("⚠️ Could not fetch targets")
        except Exception as e:
            print_error(f"⚠️ Could not check targets: {e}")
        
        console.print("\n📋 Prometheus Setup Complete!")
        console.print(f"🌐 Access Prometheus: {url}")
        console.print(f"📊 View targets: {url}/targets")
        console.print(f"📈 View metrics: {url}/metrics")
        
    except ImportError:
        print_error("❌ Error: requests library not installed")
        console.print("Install with: pip install requests")
        raise click.Abort()
    except Exception as e:
        logger.error(f"Error setting up Prometheus: {e}")
        print_error(f"❌ Error: {e}")
        raise click.Abort()


def main():
    """Main entry point for the CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
