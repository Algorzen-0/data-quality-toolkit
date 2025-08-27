"""
Real-time Streaming Processor for the Algorzen Data Quality Toolkit.

This module provides:
- Kafka-based real-time data streaming
- Stream processing for quality checks
- Real-time monitoring and alerting
- Stream analytics and aggregations
"""

from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timedelta
import logging
import json
import asyncio
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import threading
import time

from ..utils.logging import get_logger

logger = get_logger(__name__)


class StreamingProcessor:
    """Real-time streaming processor for data quality monitoring."""
    
    def __init__(self, bootstrap_servers: List[str], group_id: str = "algorzen-dqt"):
        """Initialize streaming processor with Kafka configuration."""
        try:
            self.bootstrap_servers = bootstrap_servers
            self.group_id = group_id
            self.consumers = {}
            self.producers = {}
            self.streams = {}
            self.aggregators = {}
            self.alert_handlers = {}
            self.is_running = False
            
            # Initialize Kafka producer
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3
            )
            
            logger.info(f"Streaming processor initialized with Kafka servers: {bootstrap_servers}")
            
        except Exception as e:
            logger.error(f"Failed to initialize streaming processor: {e}")
            raise
    
    def create_stream(self, stream_name: str, topic_name: str, schema: Dict[str, Any] = None) -> str:
        """Create a new data stream."""
        try:
            stream_id = f"{stream_name}_{int(time.time())}"
            
            # Create Kafka consumer for the stream
            consumer = KafkaConsumer(
                topic_name,
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"{self.group_id}-{stream_name}",
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None
            )
            
            self.consumers[stream_id] = consumer
            self.streams[stream_id] = {
                "name": stream_name,
                "topic": topic_name,
                "schema": schema,
                "created_at": datetime.utcnow(),
                "message_count": 0,
                "last_message": None,
                "status": "active"
            }
            
            logger.info(f"Stream created: {stream_id} for topic: {topic_name}")
            return stream_id
            
        except Exception as e:
            logger.error(f"Failed to create stream: {e}")
            raise
    
    def start_streaming(self, stream_id: str, callback: Callable = None):
        """Start consuming messages from a stream."""
        try:
            if stream_id not in self.consumers:
                raise ValueError(f"Stream {stream_id} not found")
            
            consumer = self.consumers[stream_id]
            stream_info = self.streams[stream_id]
            
            def consume_messages():
                try:
                    logger.info(f"Starting message consumption for stream: {stream_id}")
                    
                    for message in consumer:
                        try:
                            # Update stream statistics
                            stream_info["message_count"] += 1
                            stream_info["last_message"] = datetime.utcnow()
                            
                            # Process message
                            if callback:
                                callback(message.value, message.key, stream_id)
                            else:
                                self._default_message_processor(message.value, message.key, stream_id)
                            
                            # Update aggregators if any
                            self._update_aggregators(stream_id, message.value)
                            
                        except Exception as e:
                            logger.error(f"Error processing message in stream {stream_id}: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Stream consumption error for {stream_id}: {e}")
                    stream_info["status"] = "error"
                finally:
                    consumer.close()
            
            # Start consumption in a separate thread
            thread = threading.Thread(target=consume_messages, daemon=True)
            thread.start()
            
            self.is_running = True
            logger.info(f"Streaming started for: {stream_id}")
            
        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
            raise
    
    def _default_message_processor(self, value: Any, key: str, stream_id: str):
        """Default message processor for streams."""
        try:
            # Basic message validation
            if isinstance(value, dict):
                # Check for required fields if schema is defined
                stream_info = self.streams[stream_id]
                if stream_info.get("schema"):
                    self._validate_message_schema(value, stream_info["schema"])
                
                # Basic quality checks
                quality_score = self._calculate_stream_quality_score(value)
                
                # Log quality metrics
                logger.debug(f"Message quality score: {quality_score} for stream {stream_id}")
                
                # Trigger alerts if quality is low
                if quality_score < 0.7:
                    self._trigger_quality_alert(stream_id, value, quality_score)
            
        except Exception as e:
            logger.error(f"Default message processing error: {e}")
    
    def _validate_message_schema(self, message: Dict, schema: Dict) -> bool:
        """Validate message against defined schema."""
        try:
            for field, field_info in schema.items():
                if field_info.get("required", False) and field not in message:
                    raise ValueError(f"Required field missing: {field}")
                
                if field in message:
                    expected_type = field_info.get("type")
                    if expected_type and not isinstance(message[field], eval(expected_type)):
                        raise ValueError(f"Field {field} has wrong type. Expected {expected_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return False
    
    def _calculate_stream_quality_score(self, message: Dict) -> float:
        """Calculate quality score for a stream message."""
        try:
            score = 1.0
            
            # Check for null values
            null_count = sum(1 for v in message.values() if v is None)
            if null_count > 0:
                score -= (null_count / len(message)) * 0.3
            
            # Check for empty strings
            empty_count = sum(1 for v in message.values() if isinstance(v, str) and not v.strip())
            if empty_count > 0:
                score -= (empty_count / len(message)) * 0.2
            
            # Check data types
            type_issues = 0
            for k, v in message.items():
                if isinstance(v, (int, float)) and not np.isfinite(v):
                    type_issues += 1
            
            if type_issues > 0:
                score -= (type_issues / len(message)) * 0.2
            
            return max(0.0, score)
            
        except Exception as e:
            logger.error(f"Quality score calculation error: {e}")
            return 0.0
    
    def _trigger_quality_alert(self, stream_id: str, message: Dict, quality_score: float):
        """Trigger quality alert for low-quality messages."""
        try:
            alert = {
                "stream_id": stream_id,
                "alert_type": "low_quality",
                "quality_score": quality_score,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": "warning" if quality_score > 0.5 else "error"
            }
            
            # Send alert to alert topic
            self.producer.send(
                topic="algorzen-dqt-alerts",
                key=stream_id.encode('utf-8'),
                value=alert
            )
            
            # Call alert handlers if registered
            if stream_id in self.alert_handlers:
                for handler in self.alert_handlers[stream_id]:
                    try:
                        handler(alert)
                    except Exception as e:
                        logger.error(f"Alert handler error: {e}")
            
            logger.warning(f"Quality alert triggered for stream {stream_id}: score {quality_score}")
            
        except Exception as e:
            logger.error(f"Failed to trigger quality alert: {e}")
    
    def add_aggregator(self, stream_id: str, aggregator_name: str, config: Dict[str, Any]):
        """Add an aggregator for stream analytics."""
        try:
            if stream_id not in self.aggregators:
                self.aggregators[stream_id] = {}
            
            aggregator_id = f"{aggregator_name}_{int(time.time())}"
            
            self.aggregators[stream_id][aggregator_id] = {
                "name": aggregator_name,
                "config": config,
                "data": deque(maxlen=config.get("window_size", 1000)),
                "results": {},
                "created_at": datetime.utcnow(),
                "last_update": datetime.utcnow()
            }
            
            logger.info(f"Aggregator {aggregator_name} added to stream {stream_id}")
            return aggregator_id
            
        except Exception as e:
            logger.error(f"Failed to add aggregator: {e}")
            raise
    
    def _update_aggregators(self, stream_id: str, message: Dict):
        """Update aggregators with new message data."""
        try:
            if stream_id not in self.aggregators:
                return
            
            for aggregator_id, aggregator in self.aggregators[stream_id].items():
                try:
                    # Add message to aggregator data
                    aggregator["data"].append({
                        "message": message,
                        "timestamp": datetime.utcnow()
                    })
                    
                    # Update aggregator results
                    self._calculate_aggregator_results(stream_id, aggregator_id)
                    
                    # Update timestamp
                    aggregator["last_update"] = datetime.utcnow()
                    
                except Exception as e:
                    logger.error(f"Aggregator update error for {aggregator_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to update aggregators: {e}")
    
    def _calculate_aggregator_results(self, stream_id: str, aggregator_id: str):
        """Calculate results for a specific aggregator."""
        try:
            aggregator = self.aggregators[stream_id][aggregator_id]
            config = aggregator["config"]
            data = list(aggregator["data"])
            
            if not data:
                return
            
            aggregator_type = config.get("type", "basic")
            
            if aggregator_type == "basic":
                results = self._basic_aggregation(data, config)
            elif aggregator_type == "time_window":
                results = self._time_window_aggregation(data, config)
            elif aggregator_type == "quality_trend":
                results = self._quality_trend_aggregation(data, config)
            else:
                results = {}
            
            aggregator["results"] = results
            
        except Exception as e:
            logger.error(f"Failed to calculate aggregator results: {e}")
    
    def _basic_aggregation(self, data: List, config: Dict) -> Dict[str, Any]:
        """Perform basic aggregation on data."""
        try:
            results = {
                "message_count": len(data),
                "time_span": (data[-1]["timestamp"] - data[0]["timestamp"]).total_seconds(),
                "avg_quality_score": 0.0
            }
            
            # Calculate average quality score
            quality_scores = []
            for item in data:
                score = self._calculate_stream_quality_score(item["message"])
                quality_scores.append(score)
            
            if quality_scores:
                results["avg_quality_score"] = sum(quality_scores) / len(quality_scores)
                results["min_quality_score"] = min(quality_scores)
                results["max_quality_score"] = max(quality_scores)
            
            return results
            
        except Exception as e:
            logger.error(f"Basic aggregation error: {e}")
            return {}
    
    def _time_window_aggregation(self, data: List, config: Dict) -> Dict[str, Any]:
        """Perform time-window based aggregation."""
        try:
            window_size = config.get("window_size_seconds", 300)  # 5 minutes default
            current_time = datetime.utcnow()
            
            # Filter data within time window
            window_data = [
                item for item in data 
                if (current_time - item["timestamp"]).total_seconds() <= window_size
            ]
            
            results = {
                "window_size_seconds": window_size,
                "messages_in_window": len(window_data),
                "window_start": (current_time - timedelta(seconds=window_size)).isoformat(),
                "window_end": current_time.isoformat()
            }
            
            if window_data:
                # Calculate quality metrics for window
                quality_scores = [
                    self._calculate_stream_quality_score(item["message"]) 
                    for item in window_data
                ]
                
                results["avg_quality_score"] = sum(quality_scores) / len(quality_scores)
                results["quality_trend"] = "stable"  # Could be enhanced with trend analysis
            
            return results
            
        except Exception as e:
            logger.error(f"Time window aggregation error: {e}")
            return {}
    
    def _quality_trend_aggregation(self, data: List, config: Dict) -> Dict[str, Any]:
        """Perform quality trend analysis."""
        try:
            if len(data) < 2:
                return {}
            
            # Calculate quality scores over time
            quality_timeline = []
            for item in data:
                score = self._calculate_stream_quality_score(item["message"])
                quality_timeline.append({
                    "timestamp": item["timestamp"],
                    "score": score
                })
            
            # Sort by timestamp
            quality_timeline.sort(key=lambda x: x["timestamp"])
            
            # Calculate trend
            if len(quality_timeline) >= 2:
                first_score = quality_timeline[0]["score"]
                last_score = quality_timeline[-1]["score"]
                score_change = last_score - first_score
                
                if score_change > 0.1:
                    trend = "improving"
                elif score_change < -0.1:
                    trend = "degrading"
                else:
                    trend = "stable"
                
                # Calculate moving average
                window_size = config.get("trend_window", 10)
                if len(quality_timeline) >= window_size:
                    recent_scores = [item["score"] for item in quality_timeline[-window_size:]]
                    moving_avg = sum(recent_scores) / len(recent_scores)
                else:
                    moving_avg = sum(item["score"] for item in quality_timeline) / len(quality_timeline)
                
                results = {
                    "trend": trend,
                    "score_change": score_change,
                    "moving_average": moving_avg,
                    "data_points": len(quality_timeline),
                    "trend_window": window_size
                }
                
                return results
            
            return {}
            
        except Exception as e:
            logger.error(f"Quality trend aggregation error: {e}")
            return {}
    
    def get_aggregator_results(self, stream_id: str, aggregator_id: str) -> Dict[str, Any]:
        """Get results for a specific aggregator."""
        try:
            if stream_id in self.aggregators and aggregator_id in self.aggregators[stream_id]:
                return self.aggregators[stream_id][aggregator_id]["results"]
            return {}
        except Exception as e:
            logger.error(f"Failed to get aggregator results: {e}")
            return {}
    
    def add_alert_handler(self, stream_id: str, handler: Callable):
        """Add an alert handler for a stream."""
        try:
            if stream_id not in self.alert_handlers:
                self.alert_handlers[stream_id] = []
            
            self.alert_handlers[stream_id].append(handler)
            logger.info(f"Alert handler added to stream {stream_id}")
            
        except Exception as e:
            logger.error(f"Failed to add alert handler: {e}")
    
    def publish_message(self, topic: str, message: Dict, key: str = None) -> bool:
        """Publish a message to a Kafka topic."""
        try:
            future = self.producer.send(topic, key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"Message published to {topic}: partition {record_metadata.partition}, offset {record_metadata.offset}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    def get_stream_statistics(self, stream_id: str) -> Dict[str, Any]:
        """Get statistics for a specific stream."""
        try:
            if stream_id not in self.streams:
                return {}
            
            stream_info = self.streams[stream_id]
            stats = {
                "stream_id": stream_id,
                "name": stream_info["name"],
                "topic": stream_info["topic"],
                "status": stream_info["status"],
                "message_count": stream_info["message_count"],
                "created_at": stream_info["created_at"].isoformat(),
                "last_message": stream_info["last_message"].isoformat() if stream_info["last_message"] else None,
                "uptime_seconds": (datetime.utcnow() - stream_info["created_at"]).total_seconds()
            }
            
            # Add aggregator information
            if stream_id in self.aggregators:
                stats["aggregators"] = {
                    agg_id: {
                        "name": agg["name"],
                        "data_points": len(agg["data"]),
                        "last_update": agg["last_update"].isoformat()
                    }
                    for agg_id, agg in self.aggregators[stream_id].items()
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stream statistics: {e}")
            return {}
    
    def stop_stream(self, stream_id: str):
        """Stop a specific stream."""
        try:
            if stream_id in self.consumers:
                self.consumers[stream_id].close()
                del self.consumers[stream_id]
            
            if stream_id in self.streams:
                self.streams[stream_id]["status"] = "stopped"
            
            logger.info(f"Stream stopped: {stream_id}")
            
        except Exception as e:
            logger.error(f"Failed to stop stream: {e}")
    
    def cleanup(self):
        """Clean up streaming processor resources."""
        try:
            # Stop all streams
            for stream_id in list(self.streams.keys()):
                self.stop_stream(stream_id)
            
            # Close producer
            if hasattr(self, 'producer'):
                self.producer.close()
            
            self.is_running = False
            logger.info("Streaming processor cleaned up")
            
        except Exception as e:
            logger.error(f"Failed to cleanup streaming processor: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
