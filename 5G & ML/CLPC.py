import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import pandas as pd
from tqdm import tqdm

class FiveGUplinkPowerControl:
    """
    Implements 5G NR Uplink Power Control based on 3GPP specifications (38.213)
    with ML optimization for the power control parameters
    """
    def __init__(self, n_ues=30, simulation_steps=1000, cell_radius=500):
        # Simulation parameters
        self.n_ues = n_ues
        self.simulation_steps = simulation_steps
        self.cell_radius = cell_radius  # meters
        self.bandwidth = 20e6
        
        # 3GPP Power control parameters
        self.p0_pusch_initial = -90  # dBm, initial value for P0_PUSCH
        self.alpha_initial = 0.8     # Path loss compensation factor initial value
        self.p_max = 23              # dBm, maximum transmit power
        self.p_min = -40             # dBm, minimum transmit power
        self.delta_mcs = 0           # MCS adjustment (simplified)
        self.delta_tpc = np.zeros(n_ues)  # TPC adjustments per UE
        
        # Optimization parameters
        self.learning_rate = 0.01
        self.ml_update_interval = 50  # Update ML model every 50 steps
        
        # State initialization
        self.ue_positions = self._initialize_ue_positions()
        self.path_losses = self._calculate_path_losses()
        self.p0_pusch = np.ones(n_ues) * self.p0_pusch_initial
        self.alpha = np.ones(n_ues) * self.alpha_initial
        
        # History for ML training
        self.training_data = {
            'path_loss': [],
            'sinr': [],
            'throughput': [],
            'p0_pusch': [],
            'alpha': []
        }
        
        # Performance metrics
        self.sinr_history = []
        self.throughput_history = []
        self.power_efficiency_history = []
    
    def _initialize_ue_positions(self):
        """Random distribution of UEs in a circular cell"""
        # Random distance from center (with sqrt for uniform distribution)
        distances = self.cell_radius * np.sqrt(np.random.random(self.n_ues))
        # Random angles
        angles = 2 * np.pi * np.random.random(self.n_ues)
        # Convert to Cartesian coordinates
        x = distances * np.cos(angles)
        y = distances * np.sin(angles)
        return np.column_stack((x, y))
    
    def _calculate_path_losses(self):
        """Calculate path loss for each UE based on 3GPP Urban Macro model"""
        distances = np.sqrt(np.sum(self.ue_positions**2, axis=1))
        # Simplified path loss model: 128.1 + 37.6*log10(d/1000) for d in meters
        path_losses = 128.1 + 37.6 * np.log10(distances / 1000)
        # Add shadow fading (log-normal with 8dB standard deviation)
        shadow_fading = np.random.normal(0, 8, self.n_ues)
        return path_losses + shadow_fading
    
    def calculate_tx_power(self):
        """Calculate transmit power using the 3GPP formula for each UE"""
        # 5G NR UL power control formula: P = min(P_max, P0 + 10*log10(M) + alpha*PL + delta_mcs + delta_TPC)
        # Simplified version (M=1)
        tx_power = np.minimum(
            self.p_max,
            np.maximum(
                self.p_min,
                self.p0_pusch + self.alpha * self.path_losses + self.delta_tpc
            )
        )
        return tx_power
    
    def calculate_sinr(self, tx_power):
        """Calculate SINR for each UE"""
        # Simplified SINR calculation
        rx_power = tx_power - self.path_losses
        noise_power = -174 + 10 * np.log10(20e6)  # -174 dBm/Hz + 10*log10(BW in Hz)
        
        # Calculate interference (simplified)
        interference = np.zeros(self.n_ues)
        for i in range(self.n_ues):
            # Interference from other UEs (simplified with orthogonal allocations)
            interference[i] = -110  # Simplified fixed interference floor
        
        sinr = rx_power - (noise_power + interference)
        return sinr
    
    def calculate_throughput(self, sinr):
        """Calculate throughput based on SINR using Shannon capacity formula"""
        # Shannon capacity with bandwidth efficiency factor
        bandwidth = 20e6  # 20 MHz
        efficiency_factor = 0.6  # Practical systems achieve ~60% of Shannon capacity
        
        # Cap SINR between -10 dB and 30 dB for realistic throughput calculation
        sinr_linear = np.power(10, np.clip(sinr, -10, 30) / 10)
        throughput = bandwidth * efficiency_factor * np.log2(1 + sinr_linear) / 1e6  # in Mbps
        return throughput
    
    def calculate_power_efficiency(self, tx_power, throughput):
        """Calculate power efficiency in bits/Joule"""
        # Convert dBm to mW
        tx_power_mw = 10 ** (tx_power / 10)
        # bits per joule = bps / watts = Mbps / (mW/1000)
        power_efficiency = (throughput * 1e6) / (tx_power_mw / 1000)
        return power_efficiency
    
    def collect_training_data(self, sinr, throughput, power_consumption):
        """Collect data for ML training"""
        for i in range(self.n_ues):
            self.training_data['path_loss'].append(self.path_losses[i])
            self.training_data['sinr'].append(sinr[i])
            self.training_data['throughput'].append(throughput[i])
            self.training_data['p0_pusch'].append(self.p0_pusch[i])
            self.training_data['alpha'].append(self.alpha[i])
    
    def optimize_power_control_parameters(self):
        """Use ML to optimize P0 and alpha parameters"""
        if len(self.training_data['path_loss']) < 100:
            return  # Not enough data for training
        
        # Prepare training data
        X = pd.DataFrame({
            'path_loss': self.training_data['path_loss'],
            'current_p0': self.training_data['p0_pusch'],
            'current_alpha': self.training_data['alpha']
        })
        
        y_throughput = np.array(self.training_data['throughput'])
        y_sinr = np.array(self.training_data['sinr'])
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model for throughput optimization
        model_throughput = LinearRegression()
        model_throughput.fit(X_scaled, y_throughput)
        
        # Train model for SINR optimization
        model_sinr = LinearRegression()
        model_sinr.fit(X_scaled, y_sinr)
        
        # Update parameters for each UE
        for i in range(self.n_ues):
            # Feature vector for this UE
            features = np.array([[
                self.path_losses[i],
                self.p0_pusch[i],
                self.alpha[i]
            ]])
            features_scaled = scaler.transform(features)
            
            # Test different parameter values
            best_throughput = 0
            best_p0 = self.p0_pusch[i]
            best_alpha = self.alpha[i]
            
            # Grid search for better parameters
            for delta_p0 in [-2, -1, 0, 1, 2]:
                for delta_alpha in [-0.1, -0.05, 0, 0.05, 0.1]:
                    test_p0 = self.p0_pusch[i] + delta_p0
                    test_alpha = np.clip(self.alpha[i] + delta_alpha, 0.4, 1.0)
                    
                    # Update features with test parameters
                    test_features = np.array([[
                        self.path_losses[i],
                        test_p0,
                        test_alpha
                    ]])
                    test_features_scaled = scaler.transform(test_features)
                    
                    # Predict throughput and SINR with test parameters
                    pred_throughput = model_throughput.predict(test_features_scaled)[0]
                    pred_sinr = model_sinr.predict(test_features_scaled)[0]
                    
                    # Combined objective: maximize throughput while ensuring adequate SINR
                    if pred_throughput > best_throughput and pred_sinr > 0:
                        best_throughput = pred_throughput
                        best_p0 = test_p0
                        best_alpha = test_alpha
            
            # Update parameters with learning rate to ensure stability
            self.p0_pusch[i] += self.learning_rate * (best_p0 - self.p0_pusch[i])
            self.alpha[i] += self.learning_rate * (best_alpha - self.alpha[i])
    
    def simulate_mobility_and_channel(self):
        """Simulate UE mobility and channel variations"""
        # Add small random movements to UEs
        movement = np.random.normal(0, 10, size=(self.n_ues, 2))  # 10m standard deviation
        self.ue_positions += movement
        
        # Ensure UEs stay within cell radius
        distances = np.sqrt(np.sum(self.ue_positions**2, axis=1))
        for i in range(self.n_ues):
            if distances[i] > self.cell_radius:
                # Scale back to cell edge
                self.ue_positions[i] *= self.cell_radius / distances[i]
        
        # Update path losses
        self.path_losses = self._calculate_path_losses()
        
        # Simulate fast fading (simplified)
        fast_fading = np.random.normal(0, 5, self.n_ues)  # 5dB standard deviation
        self.path_losses += fast_fading
    
    def simulate_tpc_commands(self, sinr):
        """Simulate TPC (Transmit Power Control) commands from gNB based on SINR"""
        target_sinr = 10  # dB
        
        for i in range(self.n_ues):
            if sinr[i] < target_sinr - 5:
                # Increase power significantly if SINR is much too low
                self.delta_tpc[i] += 2
            elif sinr[i] < target_sinr - 2:
                # Increase power slightly if SINR is a bit low
                self.delta_tpc[i] += 1
            elif sinr[i] > target_sinr + 5:
                # Decrease power significantly if SINR is much too high
                self.delta_tpc[i] -= 2
            elif sinr[i] > target_sinr + 2:
                # Decrease power slightly if SINR is a bit high
                self.delta_tpc[i] -= 1
            
            # Limit TPC adjustments
            self.delta_tpc[i] = np.clip(self.delta_tpc[i], -10, 10)
    
    def run_simulation(self):
        """Run the complete power control simulation"""
        print("Running 5G NR Uplink Power Control Simulation...")
        
        avg_sinr_history = []
        avg_throughput_history = []
        avg_power_history = []
        
        for step in tqdm(range(self.simulation_steps)):
            # Calculate transmit power for all UEs
            tx_power = self.calculate_tx_power()
            
            # Calculate resulting SINR
            sinr = self.calculate_sinr(tx_power)
            
            # Calculate throughput
            throughput = self.calculate_throughput(sinr)
            
            # Calculate power efficiency
            power_efficiency = self.calculate_power_efficiency(tx_power, throughput)
            
            # Collect metrics
            avg_sinr_history.append(np.mean(sinr))
            avg_throughput_history.append(np.mean(throughput))
            avg_power_history.append(np.mean(tx_power))
            
            # Collect training data
            self.collect_training_data(sinr, throughput, tx_power)
            
            # ML-based parameter optimization (periodically)
            if step % self.ml_update_interval == 0 and step > 200:
                self.optimize_power_control_parameters()
            
            # Simulate gNB TPC commands
            self.simulate_tpc_commands(sinr)
            
            # Simulate mobility and channel variations
            self.simulate_mobility_and_channel()
        
        # Store results
        self.avg_sinr_history = avg_sinr_history
        self.avg_throughput_history = avg_throughput_history
        self.avg_power_history = avg_power_history
        
        return avg_sinr_history, avg_throughput_history, avg_power_history
    
    def plot_results(self):
        """Plot simulation results"""
        fig, axs = plt.subplots(3, 1, figsize=(12, 15))
        
        # Plot average SINR
        axs[0].plot(self.avg_sinr_history)
        axs[0].set_title('Average SINR over Time')
        axs[0].set_xlabel('Simulation Step')
        axs[0].set_ylabel('SINR (dB)')
        axs[0].grid(True)
        
        # Plot average throughput
        axs[1].plot(self.avg_throughput_history)
        axs[1].set_title('Average Throughput over Time')
        axs[1].set_xlabel('Simulation Step')
        axs[1].set_ylabel('Throughput (Mbps)')
        axs[1].grid(True)
        
        # Plot average transmit power
        axs[2].plot(self.avg_power_history)
        axs[2].set_title('Average Transmit Power over Time')
        axs[2].set_xlabel('Simulation Step')
        axs[2].set_ylabel('Transmit Power (dBm)')
        axs[2].grid(True)
        
        plt.tight_layout()
        plt.show()
        
        # Plot final UE positions
        plt.figure(figsize=(10, 10))
        plt.scatter(self.ue_positions[:, 0], self.ue_positions[:, 1], c=self.calculate_tx_power(), cmap='viridis')
        plt.colorbar(label='Transmit Power (dBm)')
        plt.title('Final UE Positions and Transmit Power')
        plt.xlabel('X position (m)')
        plt.ylabel('Y position (m)')
        circle = plt.Circle((0, 0), self.cell_radius, fill=False, color='black')
        plt.gca().add_patch(circle)
        plt.axis('equal')
        plt.grid(True)
        plt.show()
        
        # Plot P0 and alpha distribution
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.hist(self.p0_pusch)
        plt.title('P0_PUSCH Distribution')
        plt.xlabel('P0_PUSCH (dBm)')
        
        plt.subplot(1, 2, 2)
        plt.hist(self.alpha)
        plt.title('Alpha Distribution')
        plt.xlabel('Alpha')
        
        plt.tight_layout()
        plt.show()

# Example usage
if __name__ == "__main__":
    # Create and run simulation
    power_control = FiveGUplinkPowerControl(n_ues=50, simulation_steps=2000)
    sinr, throughput, power = power_control.run_simulation()
    power_control.plot_results()
    
    # Print final statistics
    print(f"Final average SINR: {sinr[-1]:.2f} dB")
    print(f"Final average throughput: {throughput[-1]:.2f} Mbps")
    print(f"Final average transmit power: {power[-1]:.2f} dBm")
    
    # Calculate improvement
    print(f"SINR improvement: {sinr[-1] - sinr[199]:.2f} dB (after ML optimization)")
    print(f"Throughput improvement: {throughput[-1] - throughput[199]:.2f} Mbps (after ML optimization)")
    print(f"Power reduction: {power[199] - power[-1]:.2f} dBm (after ML optimization)")