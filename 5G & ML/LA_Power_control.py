#!/usr/bin/env python3
"""
TelecomLayer2Library - Custom Robot Framework library for Telecom Layer 2 testing
"""

import time
import random
import logging
import numpy as np
from datetime import datetime
from collections import deque

class TelecomLayer2Library:
    """Library for testing telecom Layer 2 features like power control and link adaptation"""
    
    ROBOT_LIBRARY_SCOPE = 'SUITE'
    
    def __init__(self):
        """Initialize the library"""
        self.logger = logging.getLogger(__name__)
        self.power_control_active = False
        self.link_adaptation_active = False
        self.power_trace = []
        self.adaptation_data = []
        self.current_power = 0
        self.current_mcs = 0
        self.target_snr = 0
        self.current_snr = 0
        self.channel_quality = "good"
        self.mobility_pattern = "static"
        self.test_mode = "normal"
        
    def set_test_mode(self, mode):
        """Set the test mode"""
        self.test_mode = mode
        self.logger.info(f"Test mode set to: {mode}")
        return True
        
    def configure_logging(self, level):
        """Configure logging level"""
        logging_level = getattr(logging, level.upper())
        logging.basicConfig(level=logging_level)
        self.logger.setLevel(logging_level)
        self.logger.info(f"Logging configured to level: {level}")
        return True
    
    # Power Control Methods
    def set_tx_power(self, power_level):
        """Set transmission power level in dBm"""
        try:
            self.current_power = float(power_level)
            self.logger.info(f"Power level set to {self.current_power} dBm")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set power level: {e}")
            return False
    
    def get_current_power_level(self):
        """Get the current power level"""
        # Add small random variation to simulate real-world conditions
        variation = random.uniform(-0.2, 0.2)
        return self.current_power + variation
    
    def set_power_step_size(self, step_size):
        """Set the power step size for testing"""
        self.power_step_size = float(step_size)
        self.logger.info(f"Power step size set to {self.power_step_size} dB")
        return True
    
    def set_test_duration(self, duration):
        """Set test duration"""
        if 's' in duration:
            self.test_duration = float(duration.replace('s', ''))
        elif 'm' in duration:
            self.test_duration = float(duration.replace('m', '')) * 60
        else:
            self.test_duration = float(duration)
        self.logger.info(f"Test duration set to {self.test_duration} seconds")
        return True
    
    def enable_power_control_monitoring(self):
        """Enable power control monitoring"""
        self.power_monitoring_enabled = True
        self.logger.info("Power control monitoring enabled")
        return True
    
    def verify_power_control_configuration(self):
        """Verify power control configuration"""
        # Simple verification logic - could be expanded
        if hasattr(self, 'power_step_size') and hasattr(self, 'test_duration'):
            self.logger.info("Power control configuration verified")
            return True
        else:
            self.logger.warning("Power control configuration incomplete")
            return False
    
    def measure_power_metrics(self):
        """Measure power-related metrics"""
        # Simulate power-related measurements
        current_power = self.get_current_power_level()
        
        # Generate simulated metrics based on current power level
        snr = 30 + current_power - random.uniform(0, 3)  # Basic SNR calculation
        ber = 10 ** (-0.6 * (snr - 10)) if snr > 10 else 0.1  # Basic BER model
        throughput = min(100, 10 * snr)  # Basic throughput model (Mbps)
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'power_level': current_power,
            'snr': snr,
            'ber': ber,
            'throughput': throughput
        }
        
        return metrics
    
    def analyze_power_ramp_results(self, results):
        """Analyze power ramp test results"""
        # Extract power levels and SNR values
        power_levels = [r['power_level'] for r in results]
        snr_values = [r['snr'] for r in results]
        ber_values = [r['ber'] for r in results]
        throughput_values = [r['throughput'] for r in results]
        
        # Calculate analysis metrics
        analysis = {
            'min_power': min(power_levels),
            'max_power': max(power_levels),
            'avg_snr': sum(snr_values) / len(snr_values),
            'avg_ber': sum(ber_values) / len(ber_values),
            'max_throughput': max(throughput_values),
            'snr_gain_per_db': (max(snr_values) - min(snr_values)) / (max(power_levels) - min(power_levels)),
            'optimal_power': power_levels[throughput_values.index(max(throughput_values))]
        }
        
        return analysis
    
    def configure_power_control_mode(self, mode):
        """Configure power control mode"""
        self.power_control_mode = mode
        self.logger.info(f"Power control mode set to {mode}")
        return True
    
    def set_target_snr(self, target_snr):
        """Set target SNR for power control algorithm"""
        self.target_snr = float(target_snr)
        self.logger.info(f"Target SNR set to {self.target_snr} dB")
        return True
    
    def set_initial_snr(self, initial_snr):
        """Set initial SNR for testing"""
        self.current_snr = float(initial_snr)
        self.logger.info(f"Initial SNR set to {self.current_snr} dB")
        return True
    
    def start_power_control_algorithm(self):
        """Start power control algorithm"""
        self.power_control_active = True
        self.power_trace = []
        self.start_time = time.time()
        self.logger.info("Power control algorithm started")
        return True
    
    def stop_power_control_algorithm(self):
        """Stop power control algorithm"""
        self.power_control_active = False
        self.logger.info("Power control algorithm stopped")
        return True
    
    def get_power_control_trace(self):
        """Get power control trace data"""
        # Simulate a power control trace if it's empty
        if not self.power_trace:
            # Generate simulated trace data
            duration = 30  # simulated duration in seconds
            timestamps = np.linspace(0, duration, 30)
            
            # Start with current power and adjust towards target SNR
            power_levels = []
            snr_levels = []
            current_power = self.current_power
            current_snr = self.current_snr
            
            for t in timestamps:
                # Simple power control algorithm simulation
                snr_error = self.target_snr - current_snr
                power_adjustment = 0.1 * snr_error
                current_power += power_adjustment
                
                # Update SNR based on power adjustment (with some noise)
                current_snr = self.target_snr + (self.current_snr - self.target_snr) * np.exp(-t/10) + np.random.normal(0, 0.3)
                
                power_levels.append(current_power)
                snr_levels.append(current_snr)
                
                self.power_trace.append({
                    'timestamp': t,
                    'power_level': current_power,
                    'snr': current_snr,
                    'target_snr': self.target_snr
                })
        
        return self.power_trace
    
    def calculate_convergence_time(self, power_trace, target_snr):
        """Calculate convergence time to target SNR"""
        # Find the time when SNR is consistently within 1dB of target
        convergence_threshold = 1.0  # dB
        consecutive_threshold = 3  # number of consecutive samples
        
        consecutive_count = 0
        for i, sample in enumerate(power_trace):
            if abs(sample['snr'] - target_snr) <= convergence_threshold:
                consecutive_count += 1
                if consecutive_count >= consecutive_threshold:
                    return sample['timestamp']
            else:
                consecutive_count = 0
        
        return None  # Didn't converge within the trace
    
    def calculate_power_stability(self, power_trace):
        """Calculate power stability metric"""
        # Calculate standard deviation of power after convergence
        if len(power_trace) < 10:
            return 0.0
        
        # Use last 2/3 of trace to measure stability
        stability_section = power_trace[len(power_trace)//3:]
        power_levels = [s['power_level'] for s in stability_section]
        
        # Calculate standard deviation
        return np.std(power_levels)
    
    def calculate_snr_accuracy(self, power_trace, target_snr):
        """Calculate SNR accuracy relative to target"""
        if not power_trace:
            return 0.0
        
        # Use last half of trace
        stability_section = power_trace[len(power_trace)//2:]
        snr_values = [s['snr'] for s in stability_section]
        
        # Calculate mean absolute error
        snr_errors = [abs(snr - target_snr) for snr in snr_values]
        return sum(snr_errors) / len(snr_errors)
    
    def configure_dynamic_environment(self):
        """Configure dynamic environment for testing"""
        self.logger.info("Dynamic environment configured")
        return True
    
    def start_power_stability_measurement(self, interval):
        """Start power stability measurement"""
        self.stability_interval = float(interval.replace('s', '')) if 's' in interval else float(interval)
        self.stability_data = []
        self.stability_start_time = time.time()
        self.logger.info(f"Power stability measurement started with interval {interval}")
        return True
    
    def stop_power_stability_measurement(self):
        """Stop power stability measurement and return data"""
        # Generate simulated stability data if empty
        if not self.stability_data:
            duration = time.time() - self.stability_start_time
            timestamps = np.linspace(0, duration, int(duration / self.stability_interval))
            
            for t in timestamps:
                # Simulate power fluctuations based on environment
                power_variation = np.random.normal(0, 0.3)
                
                self.stability_data.append({
                    'timestamp': t,
                    'power_level': self.current_power + power_variation,
                    'external_interference': np.random.uniform(0, 0.5) if random.random() < 0.2 else 0
                })
        
        self.logger.info(f"Power stability measurement stopped, collected {len(self.stability_data)} samples")
        return self.stability_data
    
    def analyze_power_stability(self, stability_data):
        """Analyze power stability data"""
        if not stability_data:
            return {}
        
        power_levels = [d['power_level'] for d in stability_data]
        
        # Calculate stability metrics
        metrics = {
            'mean_power': np.mean(power_levels),
            'std_dev': np.std(power_levels),
            'min_power': min(power_levels),
            'max_power': max(power_levels),
            'peak_to_peak': max(power_levels) - min(power_levels),
            'samples': len(stability_data)
        }
        
        return metrics
    
    def verify_power_stability_requirements(self, stability_metrics):
        """Verify that power stability meets requirements"""
        # Example requirements check
        if 'std_dev' in stability_metrics and stability_metrics['std_dev'] < 1.0:
            self.logger.info("Power stability requirements met")
            return True
        else:
            self.logger.warning("Power stability requirements not met")
            return False
    
    # Link Adaptation Methods
    def set_mcs_index(self, mcs_index):
        """Set the Modulation and Coding Scheme index"""
        try:
            self.current_mcs = int(mcs_index)
            self.logger.info(f"MCS index set to {self.current_mcs}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set MCS index: {e}")
            return False
    
    def get_current_mcs(self):
        """Get the current MCS index"""
        return self.current_mcs
    
    def set_channel_quality(self, quality):
        """Set the channel quality for testing"""
        self.channel_quality = quality
        self.logger.info(f"Channel quality set to {quality}")
        return True
    
    def verify_channel_quality_configuration(self, expected_quality):
        """Verify channel quality configuration"""
        if self.channel_quality == expected_quality:
            self.logger.info("Channel quality configuration verified")
            return True
        else:
            self.logger.warning("Channel quality configuration mismatch")
            return False
    
    def configure_mobility(self, pattern):
        """Configure mobility pattern"""
        self.mobility_pattern = pattern
        self.logger.info(f"Mobility pattern set to {pattern}")
        return True
    
    def set_link_adaptation_state(self, state):
        """Enable or disable link adaptation"""
        self.link_adaptation_active = (state.lower() == 'enabled')
        self.logger.info(f"Link adaptation {state}")
        return True
    
    def verify_link_adaptation_configuration(self):
        """Verify link adaptation configuration"""
        if hasattr(self, 'channel_quality') and hasattr(self, 'mobility_pattern'):
            self