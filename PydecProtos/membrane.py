"""
Vibrating rectangular membrane simulated with leapfrog time discretization
and Dirichlet boundary condition ɸ = 0.

Wave equation ∂²ɸ/∂t² - c²∇²ɸ = f (where ɸ is velocity potential)
represented as a first-order system of differential form equations
with acoustic pressure v = ∂ɸ/∂t represented by a 0-form on the primal mesh
and particle velocity w = ∇ɸ represented by a 1-form on the primal mesh.
The boundary condition ɸ = 0 implies v = 0, but w can vary on the boundary.

(TODO: add a .md note to explain in more detail)
"""

import mesh
from sim_runner import Simulation

import numpy as np
import pydec

# shared mesh for all simulations in this file
# (TODO: load mesh from file to avoid work regenerating every time)

mesh_dim = np.pi
verts_per_side = 20
mesh_scale = mesh_dim / verts_per_side
cmp_mesh = mesh.rect_unstructured(mesh_dim, mesh_dim, mesh_scale)
cmp_complex = pydec.SimplicialComplex(cmp_mesh)


class StandingWave(Simulation):
    def __init__(self):
        # time stepping

        steps_per_unit_time = 20
        dt = 1.0 / float(steps_per_unit_time)
        sim_time_units = 6
        step_count = steps_per_unit_time * sim_time_units

        # multiplier matrix for w in the time-stepping formula for v
        v_step_mat = (
            -dt * cmp_complex[0].star_inv * cmp_complex[0].d.T * cmp_complex[1].star
        )
        # enforce boundary condition by setting rows of this matrix to 0 for boundary vertices
        for bound_edge in cmp_complex.boundary():
            for bound_vert in bound_edge.boundary():
                vert_idx = cmp_complex[0].simplex_to_index.get(bound_vert)
                v_step_mat[vert_idx, :] = 0.0
        # multiplier matrix for v in the time-stepping formula for w
        w_step_mat = dt * cmp_complex[0].d

        self.v_step_mat = v_step_mat
        self.w_step_mat = w_step_mat
        super().__init__(mesh=cmp_mesh, dt=dt, step_count=step_count, zlim=[-1.5, 1.5])

    def init_state(self):
        x_wave_count = 2
        y_wave_count = 3
        self.v = np.sin(x_wave_count * self.mesh.vertices[:, 0]) * np.sin(
            y_wave_count * self.mesh.vertices[:, 1]
        )
        # w is vector-valued, but represented in DEC as a scalar per mesh edge,
        # therefore a single scalar per edge here
        self.w = np.zeros(cmp_complex[1].num_simplices)

    def step(self):
        self.v += self.v_step_mat * self.w
        self.w += self.w_step_mat * self.v

    def get_z_data(self):
        # visualizing acoustic pressure
        return self.v


# another simulation with the same equations but different initial conditions
class MovingWave(StandingWave):
    def init_state(self):
        x = self.mesh.vertices[:, 0]
        y = self.mesh.vertices[:, 1]
        self.v = np.multiply(0.2 * np.multiply(x, x), np.sin(3 * x)) * np.sin(y)
        self.w = np.zeros(cmp_complex[1].num_simplices)


sim1 = StandingWave()
sim1.show()

sim2 = MovingWave()
sim2.show()
# sim2.save_mp4()
