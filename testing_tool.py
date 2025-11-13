"""
Testing and Evaluation Tool for Face Recognition Attendance PoC
Provides utilities for testing system performance, calibrating thresholds, and generating reports
"""

import os
import csv
import json
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import argparse
import pandas as pd
from scipy import stats
import seaborn as sns

from embedding_extractor import EmbeddingManager
from matching_engine import MatchingEngine
from logging_system import AttendanceLogger

class TestingTool:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize testing tool
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self.load_config(config_path)
        self.embedding_manager = None
        self.matching_engine = None
        self.logger = None
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except:
            return {}
    
    def initialize_components(self):
        """Initialize required components"""
        try:
            self.embedding_manager = EmbeddingManager(
                embeddings_file=self.config.get('embeddings_path', 'embeddings.json')
            )
            self.matching_engine = MatchingEngine(
                embedding_manager=self.embedding_manager,
                threshold_match=self.config.get('threshold_match', 0.70),
                distance_metric=self.config.get('distance_metric', 'cosine')
            )
            self.logger = AttendanceLogger(
                log_path=self.config.get('log_path', 'attendance.csv')
            )
        except Exception as e:
            print(f"Failed to initialize components: {e}")
    
    def analyze_attendance_logs(self, log_path: str = None) -> Dict[str, Any]:
        """
        Analyze attendance logs for performance metrics
        
        Args:
            log_path: Path to attendance CSV file
            
        Returns:
            Dictionary with analysis results
        """
        if log_path is None:
            log_path = self.config.get('log_path', 'attendance.csv')
        
        if not os.path.exists(log_path):
            return {"error": f"Log file {log_path} not found"}
        
        try:
            df = pd.read_csv(log_path)
            
            # Basic statistics
            total_records = len(df)
            unique_users = df[df['user_id'] != '']['user_id'].nunique()
            
            # Match statistics
            successful_matches = df[df['user_id'] != '']
            unknown_attempts = df[df['user_id'] == '']
            
            # Calculate rates
            match_rate = len(successful_matches) / total_records if total_records > 0 else 0
            unknown_rate = len(unknown_attempts) / total_records if total_records > 0 else 0
            
            # Liveness statistics
            liveness_passed = df[df['liveness_passed'] == True]
            liveness_rate = len(liveness_passed) / total_records if total_records > 0 else 0
            
            # Score distribution
            match_scores = successful_matches['matched_score'].astype(float)
            if len(match_scores) > 0:
                score_stats = {
                    'mean': match_scores.mean(),
                    'std': match_scores.std(),
                    'min': match_scores.min(),
                    'max': match_scores.max(),
                    'median': match_scores.median()
                }
            else:
                score_stats = {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}
            
            # Processing time statistics
            processing_times = df['processing_time_ms'].astype(float)
            if len(processing_times) > 0:
                time_stats = {
                    'mean_ms': processing_times.mean(),
                    'std_ms': processing_times.std(),
                    'p95_ms': processing_times.quantile(0.95),
                    'max_ms': processing_times.max(),
                    'fps_estimate': 1000 / processing_times.mean() if processing_times.mean() > 0 else 0
                }
            else:
                time_stats = {'mean_ms': 0, 'std_ms': 0, 'p95_ms': 0, 'max_ms': 0, 'fps_estimate': 0}
            
            # Daily statistics
            df['timestamp'] = pd.to_datetime(df['timestamp_iso'])
            df['date'] = df['timestamp'].dt.date
            
            daily_stats = df.groupby('date').agg({
                'user_id': 'count',
                'matched_score': 'mean',
                'liveness_passed': 'sum'
            }).rename(columns={
                'user_id': 'total_attempts',
                'matched_score': 'avg_score',
                'liveness_passed': 'liveness_passed'
            }).to_dict('index')
            
            return {
                'total_records': total_records,
                'unique_users': unique_users,
                'match_rate': match_rate,
                'unknown_rate': unknown_rate,
                'liveness_pass_rate': liveness_rate,
                'match_score_stats': score_stats,
                'processing_time_stats': time_stats,
                'daily_statistics': daily_stats,
                'time_range': {
                    'start': df['timestamp'].min().isoformat() if len(df) > 0 else None,
                    'end': df['timestamp'].max().isoformat() if len(df) > 0 else None
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to analyze logs: {e}"}
    
    def generate_threshold_analysis(self) -> Dict[str, Any]:
        """
        Generate threshold analysis to find optimal matching threshold
        
        Returns:
            Dictionary with threshold analysis results
        """
        try:
            # Get threshold analysis from matching engine
            analysis = self.matching_engine.get_threshold_analysis()
            
            # Suggest optimal threshold
            optimal_threshold = self.matching_engine.suggest_optimal_threshold()
            analysis['suggested_threshold'] = optimal_threshold
            
            # Calculate ROC-like statistics for different thresholds
            thresholds = np.arange(0.5, 0.95, 0.05)
            threshold_stats = []
            
            for threshold in thresholds:
                # Update matching engine threshold
                self.matching_engine.threshold_match = threshold
                
                # This would require actual test data to calculate TPR/FAR
                # For now, we'll use theoretical calculations
                stats_entry = {
                    'threshold': threshold,
                    'estimated_tpr': self.estimate_tpr(analysis, threshold),
                    'estimated_far': self.estimate_far(analysis, threshold)
                }
                threshold_stats.append(stats_entry)
            
            analysis['threshold_sweep'] = threshold_stats
            
            return analysis
            
        except Exception as e:
            return {"error": f"Failed to generate threshold analysis: {e}"}
    
    def estimate_tpr(self, analysis: Dict[str, Any], threshold: float) -> float:
        """Estimate True Positive Rate for a given threshold"""
        intra_mean = analysis['intra_user_stats']['mean']
        intra_std = analysis['intra_user_stats']['std']
        
        # Calculate probability that intra-user similarity > threshold
        if intra_std > 0:
            z_score = (threshold - intra_mean) / intra_std
            tpr = 1 - stats.norm.cdf(z_score)
        else:
            tpr = 1.0 if intra_mean >= threshold else 0.0
        
        return min(1.0, max(0.0, tpr))
    
    def estimate_far(self, analysis: Dict[str, Any], threshold: float) -> float:
        """Estimate False Accept Rate for a given threshold"""
        inter_mean = analysis['inter_user_stats']['mean']
        inter_std = analysis['inter_user_stats']['std']
        
        # Calculate probability that inter-user similarity > threshold
        if inter_std > 0:
            z_score = (threshold - inter_mean) / inter_std
            far = 1 - stats.norm.cdf(z_score)
        else:
            far = 1.0 if inter_mean >= threshold else 0.0
        
        return min(1.0, max(0.0, far))
    
    def plot_similarity_distribution(self, output_path: str = "similarity_distribution.png"):
        """
        Plot similarity score distributions
        
        Args:
            output_path: Path to save the plot
        """
        try:
            analysis = self.matching_engine.get_threshold_analysis()
            
            # Generate synthetic data for plotting (in real scenario, use actual data)
            np.random.seed(42)
            
            intra_mean = analysis['intra_user_stats']['mean']
            intra_std = analysis['intra_user_stats']['std']
            inter_mean = analysis['inter_user_stats']['mean']
            inter_std = analysis['inter_user_stats']['std']
            
            # Generate distributions
            intra_similarities = np.random.normal(intra_mean, intra_std, 1000)
            inter_similarities = np.random.normal(inter_mean, inter_std, 1000)
            
            # Clip to valid range
            intra_similarities = np.clip(intra_similarities, 0, 1)
            inter_similarities = np.clip(inter_similarities, 0, 1)
            
            # Create plot
            plt.figure(figsize=(10, 6))
            
            plt.hist(intra_similarities, bins=50, alpha=0.7, label='Same Person', color='green')
            plt.hist(inter_similarities, bins=50, alpha=0.7, label='Different People', color='red')
            
            current_threshold = self.matching_engine.threshold_match
            plt.axvline(current_threshold, color='blue', linestyle='--', 
                       label=f'Current Threshold ({current_threshold:.2f})')
            
            plt.xlabel('Similarity Score')
            plt.ylabel('Frequency')
            plt.title('Face Similarity Score Distribution')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Similarity distribution plot saved to {output_path}")
            
        except Exception as e:
            print(f"Failed to generate plot: {e}")
    
    def generate_performance_report(self, output_path: str = "performance_report.html"):
        """
        Generate comprehensive performance report
        
        Args:
            output_path: Path to save the HTML report
        """
        try:
            # Collect all analysis data
            attendance_analysis = self.analyze_attendance_logs()
            threshold_analysis = self.generate_threshold_analysis()
            
            # Generate plot
            plot_path = "similarity_distribution.png"
            self.plot_similarity_distribution(plot_path)
            
            # Create HTML report
            html_content = self.create_html_report(attendance_analysis, threshold_analysis, plot_path)
            
            with open(output_path, 'w') as f:
                f.write(html_content)
            
            print(f"Performance report generated: {output_path}")
            
        except Exception as e:
            print(f"Failed to generate performance report: {e}")
    
    def create_html_report(self, attendance_analysis: Dict[str, Any], 
                          threshold_analysis: Dict[str, Any], 
                          plot_path: str) -> str:
        """Create HTML report content"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Face Recognition Attendance PoC - Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; color: #333; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f5f5f5; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Face Recognition Attendance PoC - Performance Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        # Add attendance statistics
        if 'error' not in attendance_analysis:
            html += f"""
            <div class="section">
                <h2>Attendance Statistics</h2>
                <div class="metric">Total Records: {attendance_analysis['total_records']}</div>
                <div class="metric">Unique Users: {attendance_analysis['unique_users']}</div>
                <div class="metric">Match Rate: {attendance_analysis['match_rate']:.2%}</div>
                <div class="metric">Liveness Pass Rate: {attendance_analysis['liveness_pass_rate']:.2%}</div>
                
                <h3>Processing Performance</h3>
                <div class="metric">Average Processing Time: {attendance_analysis['processing_time_stats']['mean_ms']:.1f} ms</div>
                <div class="metric">95th Percentile: {attendance_analysis['processing_time_stats']['p95_ms']:.1f} ms</div>
                <div class="metric">Estimated FPS: {attendance_analysis['processing_time_stats']['fps_estimate']:.1f}</div>
            </div>
            """
        else:
            html += f"""
            <div class="section">
                <h2>Attendance Statistics</h2>
                <p style="color: red;">Error: {attendance_analysis['error']}</p>
            </div>
            """
        
        # Add threshold analysis
        if 'error' not in threshold_analysis:
            html += f"""
            <div class="section">
                <h2>Threshold Analysis</h2>
                <div class="metric">Current Threshold: {threshold_analysis['threshold_current']:.2f}</div>
                <div class="metric">Suggested Threshold: {threshold_analysis['suggested_threshold']:.2f}</div>
                
                <h3>Intra-user Similarity Statistics</h3>
                <p>Mean: {threshold_analysis['intra_user_stats']['mean']:.3f}, 
                   Std: {threshold_analysis['intra_user_stats']['std']:.3f}</p>
                
                <h3>Inter-user Similarity Statistics</h3>
                <p>Mean: {threshold_analysis['inter_user_stats']['mean']:.3f}, 
                   Std: {threshold_analysis['inter_user_stats']['std']:.3f}</p>
            </div>
            """
        
        # Add plot
        if os.path.exists(plot_path):
            html += f"""
            <div class="section">
                <h2>Similarity Score Distribution</h2>
                <img src="{plot_path}" alt="Similarity Distribution" style="max-width: 100%;">
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def calibrate_threshold(self, target_far: float = 0.01, 
                          confidence_level: float = 0.95) -> float:
        """
        Calibrate threshold to achieve target False Accept Rate
        
        Args:
            target_far: Target False Accept Rate
            confidence_level: Confidence level for calibration
            
        Returns:
            Calibrated threshold value
        """
        try:
            analysis = self.matching_engine.get_threshold_analysis()
            
            inter_mean = analysis['inter_user_stats']['mean']
            inter_std = analysis['inter_user_stats']['std']
            
            # Calculate threshold for target FAR using normal distribution
            z_score = stats.norm.ppf(1 - target_far)
            threshold = inter_mean + z_score * inter_std
            
            # Ensure threshold is in valid range
            threshold = max(0.5, min(0.95, threshold))
            
            print(f"Calibrated threshold for FAR={target_far:.3f}: {threshold:.3f}")
            
            return threshold
            
        except Exception as e:
            print(f"Failed to calibrate threshold: {e}")
            return self.matching_engine.threshold_match
    
    def export_test_results(self, output_path: str) -> bool:
        """
        Export test results to JSON file
        
        Args:
            output_path: Path to save results
            
        Returns:
            True if export successful
        """
        try:
            results = {
                'exported_at': datetime.now().isoformat(),
                'attendance_analysis': self.analyze_attendance_logs(),
                'threshold_analysis': self.generate_threshold_analysis(),
                'system_config': self.config
            }
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"Test results exported to {output_path}")
            return True
            
        except Exception as e:
            print(f"Failed to export test results: {e}")
            return False

def main():
    """Main testing tool"""
    parser = argparse.ArgumentParser(description="Face Recognition Testing Tool")
    parser.add_argument('--mode', choices=['analyze', 'calibrate', 'report', 'export'], 
                       default='analyze', help='Testing mode')
    parser.add_argument('--target-far', type=float, default=0.01, help='Target FAR for calibration')
    parser.add_argument('--output', help='Output path')
    parser.add_argument('--log-path', help='Path to attendance log')
    
    args = parser.parse_args()
    
    # Initialize tool
    tool = TestingTool()
    tool.initialize_components()
    
    if args.mode == 'analyze':
        analysis = tool.analyze_attendance_logs(args.log_path)
        print("Attendance Log Analysis:")
        print(json.dumps(analysis, indent=2, default=str))
        
    elif args.mode == 'calibrate':
        threshold = tool.calibrate_threshold(args.target_far)
        print(f"Calibrated threshold: {threshold:.3f}")
        
    elif args.mode == 'report':
        output_path = args.output or f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        tool.generate_performance_report(output_path)
        
    elif args.mode == 'export':
        output_path = args.output or f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        tool.export_test_results(output_path)
    
    return 0

if __name__ == "__main__":
    exit(main())