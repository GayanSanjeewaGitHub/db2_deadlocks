"""
Performance monitoring module
Tracks execution time, CPU usage, and other metrics during query execution
"""

import time
import psutil
import threading
from typing import Dict, List, Tuple
from datetime import datetime


class PerformanceMonitor:
    """
    Monitor system resources and query performance
    """
    
    def __init__(self):
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self.monitoring = False
        self.monitor_thread = None
        self.sample_interval = 0.1  # Sample every 100ms
        
    def _monitor_resources(self):
        """Background thread to monitor CPU and memory usage"""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                # Get CPU usage
                cpu_percent = psutil.cpu_percent(interval=None)
                self.cpu_samples.append(cpu_percent)
                
                # Get memory usage
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
                self.memory_samples.append(memory_mb)
                
                time.sleep(self.sample_interval)
            except Exception as e:
                print(f"Error monitoring resources: {e}")
                break
    
    def start_monitoring(self):
        """Start monitoring system resources"""
        self.cpu_samples = []
        self.memory_samples = []
        self.monitoring = True
        
        self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Dict:
        """Stop monitoring and return statistics"""
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        # Calculate statistics
        stats = {
            'cpu_avg': round(sum(self.cpu_samples) / len(self.cpu_samples), 2) if self.cpu_samples else 0,
            'cpu_max': round(max(self.cpu_samples), 2) if self.cpu_samples else 0,
            'cpu_min': round(min(self.cpu_samples), 2) if self.cpu_samples else 0,
            'memory_avg_mb': round(sum(self.memory_samples) / len(self.memory_samples), 2) if self.memory_samples else 0,
            'memory_max_mb': round(max(self.memory_samples), 2) if self.memory_samples else 0,
            'samples_collected': len(self.cpu_samples)
        }
        
        return stats


class QueryPerformanceTracker:
    """
    Track query execution performance including timing and resource usage
    """
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.results = []
    
    def execute_and_measure(self, query_name: str, query_func, *args, **kwargs) -> Dict:
        """
        Execute a query and measure its performance
        
        Args:
            query_name: Name/identifier for the query
            query_func: Function to execute (should return rows affected)
            *args, **kwargs: Arguments to pass to query_func
            
        Returns:
            Dictionary with performance metrics
        """
        print(f"\n{'='*60}")
        print(f"Executing: {query_name}")
        print(f"{'='*60}")
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Execute query with timing
        start_time = time.time()
        start_timestamp = datetime.now()
        
        try:
            rows_affected = query_func(*args, **kwargs)
            success = True
            error_message = None
        except Exception as e:
            rows_affected = 0
            success = False
            error_message = str(e)
            print(f"Error: {e}")
        
        end_time = time.time()
        end_timestamp = datetime.now()
        
        # Stop monitoring and get stats
        resource_stats = self.monitor.stop_monitoring()
        
        # Calculate duration
        duration_seconds = end_time - start_time
        duration_ms = duration_seconds * 1000
        
        # Compile results
        result = {
            'query_name': query_name,
            'start_time': start_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'end_time': end_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'duration_seconds': round(duration_seconds, 4),
            'duration_ms': round(duration_ms, 2),
            'rows_affected': rows_affected,
            'success': success,
            'error': error_message,
            'cpu_usage': {
                'average': resource_stats['cpu_avg'],
                'max': resource_stats['cpu_max'],
                'min': resource_stats['cpu_min']
            },
            'memory_usage': {
                'average_mb': resource_stats['memory_avg_mb'],
                'max_mb': resource_stats['memory_max_mb']
            },
            'samples_collected': resource_stats['samples_collected']
        }
        
        self.results.append(result)
        
        # Print summary
        print(f"\nResults:")
        print(f"  Duration: {duration_ms:.2f} ms ({duration_seconds:.4f} seconds)")
        print(f"  Rows Affected: {rows_affected:,}")
        print(f"  CPU Usage: Avg={resource_stats['cpu_avg']}%, Max={resource_stats['cpu_max']}%")
        print(f"  Memory: Avg={resource_stats['memory_avg_mb']:.2f} MB")
        print(f"  Status: {'✓ Success' if success else '✗ Failed'}")
        
        return result
    
    def get_comparison(self) -> Dict:
        """
        Compare results from multiple query executions
        
        Returns:
            Dictionary with comparison metrics
        """
        if len(self.results) < 2:
            return None
        
        # Assume we're comparing the last two results
        result1 = self.results[-2]
        result2 = self.results[-1]
        
        # Calculate differences
        time_diff = result2['duration_ms'] - result1['duration_ms']
        time_diff_percent = (time_diff / result1['duration_ms']) * 100 if result1['duration_ms'] > 0 else 0
        
        cpu_diff = result2['cpu_usage']['average'] - result1['cpu_usage']['average']
        
        comparison = {
            'query1': result1['query_name'],
            'query2': result2['query_name'],
            'time_difference_ms': round(time_diff, 2),
            'time_difference_percent': round(time_diff_percent, 2),
            'cpu_difference': round(cpu_diff, 2),
            'faster_query': result1['query_name'] if result1['duration_ms'] < result2['duration_ms'] else result2['query_name'],
            'speedup_factor': round(max(result1['duration_ms'], result2['duration_ms']) / min(result1['duration_ms'], result2['duration_ms']), 2)
        }
        
        return comparison
    
    def clear_results(self):
        """Clear all stored results"""
        self.results = []
    
    def get_all_results(self) -> List[Dict]:
        """Get all performance results"""
        return self.results


def format_performance_report(result: Dict) -> str:
    """
    Format a performance result into a readable report
    
    Args:
        result: Performance result dictionary
        
    Returns:
        Formatted string report
    """
    report = f"""
{'='*70}
PERFORMANCE REPORT: {result['query_name']}
{'='*70}

Execution Details:
  Start Time:     {result['start_time']}
  End Time:       {result['end_time']}
  Duration:       {result['duration_ms']:.2f} ms ({result['duration_seconds']:.4f} seconds)
  Rows Affected:  {result['rows_affected']:,}
  Status:         {'✓ Success' if result['success'] else '✗ Failed'}

CPU Usage:
  Average:        {result['cpu_usage']['average']:.2f}%
  Maximum:        {result['cpu_usage']['max']:.2f}%
  Minimum:        {result['cpu_usage']['min']:.2f}%

Memory Usage:
  Average:        {result['memory_usage']['average_mb']:.2f} MB
  Maximum:        {result['memory_usage']['max_mb']:.2f} MB

Monitoring:
  Samples:        {result['samples_collected']}

{'='*70}
    """
    
    if result['error']:
        report += f"\nError: {result['error']}\n"
    
    return report


def format_comparison_report(comparison: Dict) -> str:
    """
    Format a comparison result into a readable report
    
    Args:
        comparison: Comparison dictionary
        
    Returns:
        Formatted string report
    """
    report = f"""
{'='*70}
PERFORMANCE COMPARISON
{'='*70}

Query 1: {comparison['query1']}
Query 2: {comparison['query2']}

Time Difference:
  Absolute:       {comparison['time_difference_ms']:.2f} ms
  Percentage:     {comparison['time_difference_percent']:.2f}%
  
CPU Difference:   {comparison['cpu_difference']:.2f}%

Winner:           {comparison['faster_query']}
Speedup Factor:   {comparison['speedup_factor']:.2f}x

{'='*70}
    """
    
    return report
