"""
Quantum Foam Simulator - Sub-Planckian Virtual Singularities
Implements stochastic particle creation and collapse into virtual black holes
at sub-Planck scales (L < l_P).

Based on Wheeler's Quantum Foam concept with dynamic micro-black hole formation.
"""

import torch
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import warnings

@dataclass
class VirtualParticle:
    """Virtual particle that can collapse into micro-singularity"""
    position: torch.Tensor  # [4] - (t, x, y, z) in Planck units
    mass: float  # in Planck masses
    lifetime: float  # in Planck times
    birth_time: float  # when it was created
    is_singularity: bool = False  # collapsed into black hole?
    schwarzschild_radius: float = 0.0
    particle_id: int = 0  # unique ID for comparison
    
    def __post_init__(self):
        if self.is_singularity:
            self.schwarzschild_radius = 2.0 * self.mass
    
    def __eq__(self, other):
        if not isinstance(other, VirtualParticle):
            return False
        return self.particle_id == other.particle_id
    
    def __hash__(self):
        return hash(self.particle_id)


class QuantumFoam:
    """
    Quantum Foam simulator with virtual particle creation and singularity collapse.
    
    Key features:
    - Stochastic particle creation at sub-Planck scales
    - Automatic collapse when r < r_s (Schwarzschild radius)
    - Hawking evaporation of virtual singularities
    - Softening parameter to prevent numerical explosions
    - Dynamic particle list (creation/annihilation)
    """
    
    def __init__(self,
                 grid_shape: Tuple[int, int, int, int] = (8, 8, 8, 8),
                 grid_spacing: float = 1.0,  # in Planck lengths
                 creation_rate: float = 0.1,  # particles per Planck time per Planck volume
                 planck_density_threshold: float = 1.0,  # ρ/ρ_P for creation
                 collapse_threshold: float = 1.0,  # r/r_s for collapse
                 softening_length: float = 0.1,  # ε in Planck lengths
                 enable_hawking_evaporation: bool = True,
                 dtype=torch.float64,
                 device='cpu',
                 random_seed: Optional[int] = None):
        
        self.grid_shape = grid_shape
        self.grid_spacing = grid_spacing
        self.creation_rate = creation_rate
        self.planck_density_threshold = planck_density_threshold
        self.collapse_threshold = collapse_threshold
        self.softening_length = softening_length
        self.enable_hawking = enable_hawking_evaporation
        self.dtype = dtype
        self.device = device
        
        # Random number generator (for reproducibility and Lyapunov analysis)
        self.rng = np.random.RandomState(random_seed)
        self.random_seed = random_seed
        
        # Virtual particle registry
        self.virtual_particles: List[VirtualParticle] = []
        
        # Particle ID counter
        self._next_particle_id = 0
        
        # Statistics
        self.stats = {
            'total_created': 0,
            'total_collapsed': 0,
            'total_evaporated': 0,
            'current_particles': 0,
            'current_singularities': 0
        }
        
        # Physical constants (Planck units: G = c = ℏ = k_B = 1)
        self.G = 1.0
        self.c = 1.0
        self.hbar = 1.0
        
        print("="*70)
        print("QUANTUM FOAM SIMULATOR v3.0 - Singularity Foam Edition")
        print("="*70)
        print(f"Grid: {grid_shape}, spacing: {grid_spacing} l_P")
        print(f"Creation rate: {creation_rate} per t_P per V_P")
        print(f"Collapse threshold: {collapse_threshold} r_s")
        print(f"Softening length: {softening_length} l_P")
        print(f"Hawking evaporation: {'Enabled' if self.enable_hawking else 'Disabled'}")
        print("="*70)
    
    def generate_gaussian_random_field(self, shape: Tuple[int, ...], power: float = 2.0) -> torch.Tensor:
        """
        Generate Gaussian Random Field (GRF) for more physical metric fluctuations.
        P(k) ~ k^(-power)
        """
        # Frequency grid
        dims = len(shape)
        freqs = [torch.fft.fftfreq(n, dtype=self.dtype, device=self.device) for n in shape]
        mesh = torch.meshgrid(*freqs, indexing='ij')
        
        # Distance from origin in k-space
        k_sq = sum(m**2 for m in mesh)
        k_sq[0, 0, 0, 0] = 1e-10 # avoid div by zero
        
        # Power spectrum
        pk = k_sq**(-power / 2.0)
        
        # Random complex coefficients
        noise = torch.randn(shape, dtype=torch.complex128, device=self.device)
        
        # Filter noise
        field_fft = noise * torch.sqrt(pk)
        
        # Inverse FFT
        field = torch.real(torch.fft.ifftn(field_fft))
        
        # Normalize
        field = (field - field.mean()) / field.std()
        return field

    def add_physical_fluctuations(self, g_minkowski: torch.Tensor, amplitude: float = 0.1) -> torch.Tensor:
        """
        Replace naive random noise with GRF-based physical fluctuations.
        """
        shape = g_minkowski.shape[:4]
        
        # Generate fluctuations for each component (or apply to the trace)
        # Using 4D GRF
        fluctuations = self.generate_gaussian_random_field(shape, power=3.0)
        
        # Apply to metric
        return g_minkowski + fluctuations.unsqueeze(-1).unsqueeze(-1) * amplitude
    
    def compute_local_energy_density(self, 
                                    position: torch.Tensor,
                                    metric_field) -> float:
        """
        Compute local energy density at position from metric fluctuations.
        
        ρ ~ |δg_μν|² / l_P⁴
        
        Args:
            position: [4] coordinates
            metric_field: MetricField object
        Returns:
            ρ: energy density in Planck density units
        """
        # Get metric at position
        g = metric_field.interpolate_metric(position)
        
        # Minkowski metric
        eta = torch.diag(torch.tensor([-1.0, 1.0, 1.0, 1.0], 
                                      dtype=self.dtype, device=self.device))
        
        # Metric perturbation
        delta_g = g - eta
        
        # Energy density from fluctuations
        rho = torch.sum(delta_g**2).item()
        
        return rho

    def should_create_particle(self, 
                               position: torch.Tensor,
                               metric_field,
                               dt: float) -> bool:
        """
        Stochastic decision: should we create a virtual particle here?
        
        Creation probability ~ ρ/ρ_P * creation_rate * dt * dV
        
        Args:
            position: [4] coordinates
            metric_field: MetricField object
            dt: time step
        Returns:
            bool: True if particle should be created
        """
        # Local energy density
        rho = self.compute_local_energy_density(position, metric_field)
        
        # Volume element
        dV = self.grid_spacing**3
        
        # Creation probability
        prob = (rho / self.planck_density_threshold) * self.creation_rate * dt * dV
        
        # Stochastic decision (using instance RNG for reproducibility)
        return self.rng.random() < prob

    
    def create_virtual_particle(self, 
                               position: torch.Tensor,
                               current_time: float) -> VirtualParticle:
        """
        Create a virtual particle with random mass and lifetime.
        
        Mass distribution: m ~ m_P (Planck scale)
        Lifetime: τ ~ ℏ/(mc²) = 1/m in Planck units
        
        Args:
            position: [4] birth position
            current_time: current simulation time
        Returns:
            VirtualParticle
        """
        # Random mass around Planck mass (log-normal distribution)
        log_mass = self.rng.normal(0.0, 0.5)  # mean=0, std=0.5
        mass = np.exp(log_mass)  # m ~ 0.6 to 1.6 m_P typically
        
        # Lifetime from uncertainty principle: Δt ~ ℏ/ΔE ~ 1/m
        lifetime = 1.0 / mass
        
        particle = VirtualParticle(
            position=position.clone(),
            mass=mass,
            lifetime=lifetime,
            birth_time=current_time,
            is_singularity=False,
            particle_id=self._next_particle_id
        )
        
        self._next_particle_id += 1
        self.virtual_particles.append(particle)
        self.stats['total_created'] += 1
        self.stats['current_particles'] += 1
        
        return particle
    
    def check_collapse_condition(self, 
                                 particle1: VirtualParticle,
                                 particle2: VirtualParticle) -> bool:
        """
        Check if two particles should collapse into virtual singularity.
        
        Collapse condition: r < collapse_threshold * r_s
        where r_s = 2G(m1 + m2)/c² = 2(m1 + m2) in Planck units
        
        Args:
            particle1, particle2: VirtualParticle objects
        Returns:
            bool: True if should collapse
        """
        # Distance between particles
        dr = particle1.position[1:] - particle2.position[1:]  # spatial part
        r = torch.sqrt(torch.sum(dr**2)).item()
        
        # Combined Schwarzschild radius
        total_mass = particle1.mass + particle2.mass
        r_s = 2.0 * total_mass
        
        # Collapse condition
        return r < self.collapse_threshold * r_s
    
    def collapse_to_singularity(self, 
                               particle1: VirtualParticle,
                               particle2: VirtualParticle) -> VirtualParticle:
        """
        Collapse two particles into a virtual micro-black hole.
        
        Conservation laws:
        - Total mass: M = m1 + m2
        - Center of mass position
        - Lifetime: τ_evap ~ M³ (Hawking evaporation time)
        
        Args:
            particle1, particle2: particles to merge
        Returns:
            VirtualParticle (singularity)
        """
        # Total mass
        total_mass = particle1.mass + particle2.mass
        
        # Center of mass position
        com_position = (particle1.mass * particle1.position + 
                       particle2.mass * particle2.position) / total_mass
        
        # Hawking evaporation time: t_evap ~ 5120π M³
        evaporation_time = 5120.0 * np.pi * total_mass**3
        
        # Create singularity
        singularity = VirtualParticle(
            position=com_position,
            mass=total_mass,
            lifetime=evaporation_time,
            birth_time=max(particle1.birth_time, particle2.birth_time),
            is_singularity=True,
            particle_id=self._next_particle_id
        )
        
        self._next_particle_id += 1
        self.stats['total_collapsed'] += 1
        self.stats['current_singularities'] += 1
        
        return singularity
    
    def compute_hawking_evaporation(self, 
                                   singularity: VirtualParticle,
                                   dt: float) -> float:
        """
        Compute mass loss due to Hawking radiation.
        
        dM/dt = -L/c² = -1/(15360π M²) in Planck units
        
        Args:
            singularity: VirtualParticle (must be singularity)
            dt: time step
        Returns:
            dM: mass change (negative)
        """
        if not singularity.is_singularity:
            return 0.0
        
        # Hawking luminosity
        L = 1.0 / (15360.0 * np.pi * singularity.mass**2)
        
        # Mass loss
        dM = -L * dt
        
        return dM
    
    def compute_vacuum_polarization_pressure(self, 
                                            position: torch.Tensor,
                                            metric_field) -> float:
        """
        Compute quantum vacuum polarization pressure (противодействие сжатию).
        
        На малых масштабах вакуум создает "эффект пружины":
        P_vac ~ ρ_vac ~ (ℏc/L⁴) в планковских единицах
        
        Это предотвращает полное схлопывание пространства.
        
        Args:
            position: [4] coordinates
            metric_field: MetricField object
        Returns:
            P_vac: vacuum pressure (positive = repulsive)
        """
        # Вычисляем локальную кривизну
        g = metric_field.interpolate_metric(position)
        
        # Ricci scalar (упрощенная оценка через след метрики)
        g_trace = torch.trace(g).item()
        
        # Vacuum energy density: ρ_vac ~ R (пропорционально кривизне)
        # На планковских масштабах: ρ_vac ~ 1/L⁴
        rho_vac = abs(g_trace - 2.0)  # отклонение от плоского пространства
        
        # Vacuum pressure (уравнение состояния: P = -ρ для космологической константы)
        # Но для квантовых флуктуаций: P = +ρ/3 (radiation-like)
        P_vac = rho_vac / 3.0
        
        return P_vac
    
    def compute_casimir_force(self, 
                             particle1: VirtualParticle,
                             particle2: VirtualParticle) -> float:
        """
        Compute Casimir force between two particles (квантовая сила отталкивания).
        
        F_Casimir = -π²ℏc/(240 r⁴) в обычных единицах
        В планковских единицах: F ~ -1/r⁴
        
        Отрицательная сила = притяжение на больших расстояниях
        Положительная сила = отталкивание на малых расстояниях (регуляризация)
        
        Args:
            particle1, particle2: VirtualParticle objects
        Returns:
            F: Casimir force magnitude (positive = repulsive)
        """
        # Distance
        dr = particle1.position[1:] - particle2.position[1:]
        r = torch.sqrt(torch.sum(dr**2)).item()
        
        # Regularization
        r_reg = max(r, self.softening_length)
        
        # Casimir force (упрощенная модель)
        # На r < l_P: отталкивание (предотвращает коллапс)
        # На r > l_P: притяжение (стандартный эффект Казимира)
        if r < 1.0:  # sub-Planckian
            # Repulsive quantum pressure
            F_casimir = 1.0 / r_reg**4
        else:
            # Attractive Casimir effect
            F_casimir = -1.0 / r_reg**4
        
        return F_casimir
    
    def compute_quantum_stress_energy_tensor(self, 
                                            position: torch.Tensor,
                                            metric_field) -> torch.Tensor:
        """
        Compute quantum vacuum stress-energy tensor.
        
        T^μν_vac = <T^μν> включает:
        1. Vacuum energy density: T^00 = ρ_vac
        2. Vacuum pressure: T^ii = -P_vac (изотропное давление)
        3. Поляризация вакуума
        
        Args:
            position: [4] coordinates
            metric_field: MetricField object
        Returns:
            T_vac: [4, 4] stress-energy tensor
        """
        # Vacuum pressure
        P_vac = self.compute_vacuum_polarization_pressure(position, metric_field)
        
        # Stress-energy tensor (diagonal, изотропный)
        T_vac = torch.zeros(4, 4, dtype=self.dtype, device=self.device)
        
        # Energy density (T^00)
        T_vac[0, 0] = P_vac
        
        # Pressure (T^ii = -P для космологической константы)
        # Но для квантовых флуктуаций: T^ii = +P/3
        for i in range(1, 4):
            T_vac[i, i] = P_vac / 3.0
        
        return T_vac
    
    def apply_quantum_pressure_force(self, 
                                    particle: VirtualParticle,
                                    metric_field,
                                    dt: float) -> torch.Tensor:
        """
        Apply quantum pressure force to particle (противодействие коллапсу).
        
        F_quantum = -∇P_vac
        
        Это создает "эффект пружины" на малых масштабах.
        
        Args:
            particle: VirtualParticle
            metric_field: MetricField object
            dt: time step
        Returns:
            dv: velocity change [3] (spatial)
        """
        # Compute pressure gradient (finite differences)
        h = 0.1 * self.grid_spacing
        
        grad_P = torch.zeros(3, dtype=self.dtype, device=self.device)
        
        for i in range(3):
            pos_plus = particle.position.clone()
            pos_minus = particle.position.clone()
            pos_plus[i+1] += h
            pos_minus[i+1] -= h
            
            P_plus = self.compute_vacuum_polarization_pressure(pos_plus, metric_field)
            P_minus = self.compute_vacuum_polarization_pressure(pos_minus, metric_field)
            
            grad_P[i] = (P_plus - P_minus) / (2 * h)
        
        # Force: F = -∇P (pressure gradient)
        F_quantum = -grad_P
        
        # Acceleration: a = F/m
        a_quantum = F_quantum / particle.mass
        
        # Velocity change
        dv = a_quantum * dt
        
        return dv
    
    def evolve_foam(self, 
                   metric_field,
                   current_time: float,
                   dt: float,
                   enable_quantum_pressure: bool = True) -> Dict:
        """
        Evolve quantum foam for one time step with QUANTUM PRESSURE.
        
        Steps:
        1. Stochastic particle creation
        2. Check collapse conditions (with Casimir force)
        3. Apply quantum pressure (противодействие коллапсу)
        4. Hawking evaporation
        5. Remove expired particles
        
        Args:
            metric_field: MetricField object
            current_time: current simulation time
            dt: time step
            enable_quantum_pressure: enable vacuum polarization pressure
        Returns:
            dict with evolution statistics
        """
        created_count = 0
        collapsed_count = 0
        evaporated_count = 0
        
        # 1. Stochastic particle creation
        # Sample random positions in grid
        n_samples = int(self.creation_rate * dt * np.prod(self.grid_shape))
        
        for _ in range(n_samples):
            # Random position in grid
            t_idx = self.rng.randint(0, self.grid_shape[0])
            x_idx = self.rng.randint(0, self.grid_shape[1])
            y_idx = self.rng.randint(0, self.grid_shape[2])
            z_idx = self.rng.randint(0, self.grid_shape[3])
            
            # Convert to physical coordinates
            position = torch.tensor([
                t_idx * self.grid_spacing,
                (x_idx - self.grid_shape[1]/2) * self.grid_spacing,
                (y_idx - self.grid_shape[2]/2) * self.grid_spacing,
                (z_idx - self.grid_shape[3]/2) * self.grid_spacing
            ], dtype=self.dtype, device=self.device)
            
            if self.should_create_particle(position, metric_field, dt):
                self.create_virtual_particle(position, current_time)
                created_count += 1
        
        # 2. Check collapse conditions (pairwise)
        particles_to_remove = []
        singularities_to_add = []
        
        for i in range(len(self.virtual_particles)):
            for j in range(i + 1, len(self.virtual_particles)):
                p1 = self.virtual_particles[i]
                p2 = self.virtual_particles[j]
                
                # Skip if already marked for removal
                if p1 in particles_to_remove or p2 in particles_to_remove:
                    continue
                
                # Check collapse (with Casimir force modification)
                if self.check_collapse_condition(p1, p2):
                    # Compute Casimir force (может предотвратить коллапс)
                    F_casimir = self.compute_casimir_force(p1, p2)
                    
                    # If repulsive Casimir force is strong, prevent collapse
                    if F_casimir < 0.5:  # threshold for collapse prevention
                        singularity = self.collapse_to_singularity(p1, p2)
                        singularities_to_add.append(singularity)
                        particles_to_remove.extend([p1, p2])
                        collapsed_count += 1
        
        # Remove collapsed particles
        for p in particles_to_remove:
            if p in self.virtual_particles:
                self.virtual_particles.remove(p)
                self.stats['current_particles'] -= 1
        
        # Add new singularities
        self.virtual_particles.extend(singularities_to_add)
        self.stats['current_particles'] += len(singularities_to_add)
        
        # 3. Apply quantum pressure (противодействие коллапсу)
        if enable_quantum_pressure:
            for particle in self.virtual_particles:
                if not particle.is_singularity:  # Only for regular particles
                    # Quantum pressure creates "spring effect"
                    dv = self.apply_quantum_pressure_force(particle, metric_field, dt)
                    # Update position (simplified: assume velocity ~ dv)
                    particle.position[1:] += dv * dt
        
        # 4. Hawking evaporation
        if self.enable_hawking:
            for particle in self.virtual_particles:
                if particle.is_singularity:
                    dM = self.compute_hawking_evaporation(particle, dt)
                    particle.mass += dM
                    
                    # Update Schwarzschild radius
                    particle.schwarzschild_radius = 2.0 * particle.mass
        
        # 5. Remove expired particles
        expired = []
        for particle in self.virtual_particles:
            age = current_time - particle.birth_time
            
            # Check lifetime or mass depletion
            if age > particle.lifetime or particle.mass < 0.01:
                expired.append(particle)
                if particle.is_singularity:
                    evaporated_count += 1
                    self.stats['total_evaporated'] += 1
                    self.stats['current_singularities'] -= 1
        
        for p in expired:
            if p in self.virtual_particles:
                self.virtual_particles.remove(p)
                self.stats['current_particles'] -= 1
        
        return {
            'created': created_count,
            'collapsed': collapsed_count,
            'evaporated': evaporated_count,
            'total_particles': len(self.virtual_particles),
            'singularities': sum(1 for p in self.virtual_particles if p.is_singularity)
        }
    
    def compute_regularized_force(self, 
                                 r: float,
                                 m1: float,
                                 m2: float) -> float:
        """
        Compute gravitational force with softening to prevent singularities.
        
        F = G m1 m2 / (r² + ε²)
        
        Args:
            r: distance
            m1, m2: masses
        Returns:
            F: force magnitude
        """
        epsilon_sq = self.softening_length**2
        F = self.G * m1 * m2 / (r**2 + epsilon_sq)
        return F
    
    def get_statistics(self) -> Dict:
        """Get current foam statistics"""
        return {
            **self.stats,
            'average_mass': np.mean([p.mass for p in self.virtual_particles]) if self.virtual_particles else 0.0,
            'average_lifetime': np.mean([p.lifetime for p in self.virtual_particles]) if self.virtual_particles else 0.0,
            'singularity_fraction': self.stats['current_singularities'] / max(1, self.stats['current_particles'])
        }
    
    def visualize_foam_state(self) -> str:
        """Generate text visualization of foam state"""
        lines = []
        lines.append("="*70)
        lines.append("QUANTUM FOAM STATE")
        lines.append("="*70)
        lines.append(f"Total particles: {self.stats['current_particles']}")
        lines.append(f"  Regular: {self.stats['current_particles'] - self.stats['current_singularities']}")
        lines.append(f"  Singularities: {self.stats['current_singularities']}")
        lines.append(f"\nLifetime statistics:")
        lines.append(f"  Created: {self.stats['total_created']}")
        lines.append(f"  Collapsed: {self.stats['total_collapsed']}")
        lines.append(f"  Evaporated: {self.stats['total_evaporated']}")
        
        if self.virtual_particles:
            lines.append(f"\nCurrent particles:")
            for i, p in enumerate(self.virtual_particles[:10]):  # Show first 10
                ptype = "SINGULARITY" if p.is_singularity else "particle"
                lines.append(f"  [{i}] {ptype}: m={p.mass:.3f} m_P, "
                           f"r_s={p.schwarzschild_radius:.3f} l_P" if p.is_singularity 
                           else f"  [{i}] {ptype}: m={p.mass:.3f} m_P")
            
            if len(self.virtual_particles) > 10:
                lines.append(f"  ... and {len(self.virtual_particles) - 10} more")
        
        lines.append("="*70)
        return "\n".join(lines)


def demonstrate_quantum_foam():
    """Demonstration of quantum foam with virtual singularities"""
    print("\n" + "="*70)
    print("QUANTUM FOAM DEMONSTRATION - Sub-Planckian Dynamics")
    print("="*70 + "\n")
    
    # Import engine for metric field
    from engine import MetricField
    
    # Create simple Minkowski metric
    grid_shape = (8, 8, 8, 8)
    grid_spacing = 1.0
    
    # Minkowski metric
    g_minkowski = torch.zeros((*grid_shape, 4, 4), dtype=torch.float64)
    # Minkowski metric
    g_minkowski = torch.zeros((*grid_shape, 4, 4), dtype=torch.float64)
    for it in range(grid_shape[0]):
        for ix in range(grid_shape[1]):
            for iy in range(grid_shape[2]):
                for iz in range(grid_shape[3]):
                    g_minkowski[it, ix, iy, iz] = torch.diag(
                        torch.tensor([-1.0, 1.0, 1.0, 1.0], dtype=torch.float64)
                    )
    
    # Create quantum foam instance
    foam = QuantumFoam(
        grid_shape=grid_shape,
        grid_spacing=grid_spacing,
        creation_rate=0.5,
        collapse_threshold=1.0,
        softening_length=0.1,
        enable_hawking_evaporation=True
    )
    
    # Add physical fluctuations using GRF
    fluctuation_amplitude = 0.1
    g_minkowski = foam.add_physical_fluctuations(g_minkowski, amplitude=fluctuation_amplitude)
    
    metric_field = MetricField(g_minkowski, grid_spacing)
    
    # Evolve foam
    dt = 0.1  # Planck times
    n_steps = 50
    
    print(f"\nEvolving foam for {n_steps} steps (dt = {dt} t_P)...\n")
    
    for step in range(n_steps):
        current_time = step * dt
        
        stats = foam.evolve_foam(metric_field, current_time, dt)
        
        if step % 10 == 0:
            print(f"Step {step}: t = {current_time:.2f} t_P")
            print(f"  Created: {stats['created']}, Collapsed: {stats['collapsed']}, "
                  f"Evaporated: {stats['evaporated']}")
            print(f"  Total: {stats['total_particles']} particles "
                  f"({stats['singularities']} singularities)")
    
    # Final statistics
    print("\n" + foam.visualize_foam_state())
    
    final_stats = foam.get_statistics()
    print(f"\nFinal Statistics:")
    print(f"  Average mass: {final_stats['average_mass']:.3f} m_P")
    print(f"  Average lifetime: {final_stats['average_lifetime']:.3f} t_P")
    print(f"  Singularity fraction: {final_stats['singularity_fraction']:.1%}")
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)


if __name__ == "__main__":
    demonstrate_quantum_foam()
