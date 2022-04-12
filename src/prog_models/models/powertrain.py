# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from prog_models import PrognosticsModel

def update_Cq(params):
    return {
        'C_q': params['c_q'] * params['rho'] * pow(params['D'], 5)
    }


class Powertrain(PrognosticsModel):
    """
    Powertrain model composed of ESC and DC motor (with the option to add propeller load using parameter Cq).
    The powertrain model is used to simulate the motor dynamics including the effect of the speed controller and pulse-width modulation.

    Parameters for a standard propeller for commercial UAV are also added to the powertrain model, so that the load torque 
    acting on the motor can be computed. At this stage, the propeller is modeled simply as a load torque proportional to the square of the rotor speed. 
    When simulating the full PWM signal, this model needs a very small time step size (e.g., dt=1e-5) to show the full dynamics.
    Faster simulations can be achieved by ignoring the PWM square wave and acting directing on the input voltage. For example, modulating 
    the input voltage to replicate the behavior of a throttle.

    References:
    Matteo Corbetta, Chetan S. Kulkarni. An approach for uncertainty quantification and management of unmanned aerial vehicle health. 
    Annual Conference of the PHM Society, Scottsdale, AZ, 2019. http://papers.phmsociety.org/index.php/phmconf/article/view/847

    George E. Gorospe Jr, Chetan S. Kulkarni, Edward Hogge, Andrew Hsu, and Natalie Ownby. A Study of the Degradation of Electronic Speed Controllers forBrushless DC Motors.
    Asia Pacific Conference of the Prognostics and Health Management Society, 2017. https://ntrs.nasa.gov/citations/20200000579

    Events: (0)
        | None

    Inputs: (2)
        | duty :        Duty cycle [-], percentage the input is "on" (i.e., voltage is supplied). 0 = no voltage supply (always closed), 1 = 100% voltage supply (always open).
        | v :           voltage [V], voltage input from Battery (after DC converter, should be constant).

    States: (5)
        | v_a :         3-phase voltage value, first phase, [V], input to the motor
        | v_b :         3-phase voltage value, second phase, [V], input to the motor
        | v_c :         3-phase voltage value, third phase [V], input to the motor
        | t :           time value [s].
        | i_a :         3-phase current value, first phase [A], motor state
        | i_b :         3-phase current value, second phase [A], motor state
        | i_c :         3-phase current value, third phase [A], motor state
        | v_rot :       Motor angular velocity [rad/s]
        | theta :       Motor rotor position [rad]

    Outputs: (2)
        | v_rot :       Motor angular velocity [rad/s]
        | theta :       Motor rotor position [rad]

    Model Configuration Parameters:
        | process_noise :       Process noise (applied at dx/next_state). 
                                Can be number (e.g., .2) applied to every state, a dictionary of values for each 
                                state (e.g., {'x1': 0.2, 'x2': 0.3}), or a function (x) -> x
        | process_noise_dist :  Optional, distribution for process noise (e.g., normal, uniform, triangular)
        | measurement_noise :   Measurement noise (applied in output eqn)
                                Can be number (e.g., .2) applied to every output, a dictionary of values for each 
                                output (e.g., {'z1': 0.2, 'z2': 0.3}), or a function (z) -> z
        | measurement_noise_dist :  Optional, distribution for measurement noise (e.g., normal, uniform, triangular)
        | c_q :                     Dimensionless coefficient of torque of the propeller [-], (APC data, derived).
        | rho :                     Air density [Kg/m^3].
        | D:                        Propeller diameter [m].

    """
    inputs = ['duty', 'v']
    states = ['v_a', 'v_b', 'v_c', 't', 'i_a', 'i_b', 'i_c', 'v_rot', 'theta']
    outputs = ['v_rot', 'theta']
    param_callbacks = {
        'c_q': [update_Cq],
        'rho': [update_Cq],
        'D': [update_Cq],
    }

    default_parameters = {
        # Load parameters 
        'c_q': 0.00542, # coefficient of torque (APC data, derived) [dimensionless]
        'rho': 1.225, # (Kg/m^3)
        'D': 0.381, # (m)
    }

    def __init__(self, esc, motor, **kwargs):
        super().__init__(**kwargs)
        self.esc = esc
        self.motor = motor

    def __eq__(self, other):
        return (
            super().__eq__(other) and
            self.esc == other.esc and
            self.motor == other.motor
        )

    def initialize(self, u=None, z=None):
        x0 = self.esc.initialize(u=u, z=z)
        x0.update(self.motor.initialize(u=u, z=z))

        return self.StateContainer(x0)

    def next_state(self, x, u, dt):
        x_esc = self.esc.StateContainer(x)
        u_esc = {
            'duty': u['duty'], 
            'theta': x['theta'],
            'v': u['v']}
        u_esc = self.esc.InputContainer(u_esc)
        x_esc = self.esc.next_state(x_esc, u_esc, dt)

        x_motor = self.motor.StateContainer(x)
        u_motor = {
            'v_a': x_esc['v_a'],
            'v_b': x_esc['v_b'],
            'v_c': x_esc['v_c'],
            't_l': self.parameters['C_q']*x['v_rot']**2
        }
        x_motor = self.motor.next_state(x_motor, u_motor, dt)

        x_esc.update(x_motor)

        return self.StateContainer(x_esc)

    def output(self, x):
        return self.OutputContainer(
            {
                'v_rot': x['v_rot'], 
                'theta': x['theta']})
