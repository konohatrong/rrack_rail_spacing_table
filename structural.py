import numpy as np

def calculate_Mn(breaking_load_kn, test_span_m, safety_factor=1.0):
    """
    Calculates Nominal Moment Capacity (Mn).
    Mn = (P_break * L_test) / 4 / SF
    """
    mn_test = (breaking_load_kn * test_span_m) / 4.0
    return mn_test / safety_factor

def solve_continuous_beam_exact(span_length, num_spans, w_load):
    """
    Engine: Solves Indeterminate Continuous Beam using Matrix Method (System of Linear Equations).
    Method: Clapeyron's Three-Moment Theorem for equal spans.
    
    Returns exact arrays for x, shear(V), moment(M), and reactions(R).
    """
    L = span_length
    w = w_load
    n_supports = num_spans + 1
    
    # 1. Solve for Support Moments (M) using Matrix [A][M] = [B]
    if num_spans == 1:
        M_supports = np.array([0.0, 0.0])
    else:
        n_internal = num_spans - 1
        A = np.zeros((n_internal, n_internal))
        for i in range(n_internal):
            A[i, i] = 4.0
            if i > 0: A[i, i-1] = 1.0
            if i < n_internal - 1: A[i, i+1] = 1.0
        B = np.full(n_internal, -0.5 * w * L**2)
        
        if n_internal > 0:
            M_internal = np.linalg.solve(A, B)
            M_supports = np.concatenate(([0], M_internal, [0]))
        else:
            M_supports = np.zeros(n_supports)

    # 2. Calculate Reactions (R) & Shears
    R = np.zeros(n_supports)
    V_right = np.zeros(num_spans)
    V_left = np.zeros(num_spans)
    
    for i in range(num_spans):
        V_right[i] = (w * L**2 / 2 - M_supports[i] + M_supports[i+1]) / L
        V_left[i] = w * L - V_right[i]
        
    R[0] = V_right[0]
    R[-1] = V_left[-1]
    for i in range(1, num_spans):
        R[i] = V_left[i-1] + V_right[i]

    # 3. Generate Plotting Data
    points_per_span = 50
    x_plot = []
    shear_plot = []
    moment_plot = []
    
    for i in range(num_spans):
        x_local = np.linspace(0, L, points_per_span)
        v_local = V_right[i] - w * x_local
        m_local = M_supports[i] + V_right[i] * x_local - (w * x_local**2) / 2
        x_global = x_local + i * L
        
        x_plot.extend(x_global)
        shear_plot.extend(v_local)
        moment_plot.extend(m_local)

    # Convert to numpy arrays for max calculation
    m_arr = np.array(moment_plot)
    v_arr = np.array(shear_plot)

    return {
        'max_moment': np.max(np.abs(m_arr)), # Absolute max moment
        'max_shear': np.max(np.abs(v_arr)),  # Absolute max shear (ADDED THIS)
        'moment_array': m_arr,
        'shear_array': v_arr,
        'x_array': np.array(x_plot),
        'reactions': R,
        'rxn_edge': R[0],
        'rxn_internal': np.max(R[1:-1]) if len(R) > 2 else (R[0] if len(R)==2 else 0),
        'rxn_max': np.max(R)
    }

def optimize_span(Mn, w_load, num_spans, max_span=4.0, clamp_capacity=None):
    """
    Optimizes span based on:
    1. Rail Bending Capacity (Mn)
    2. Clamp Pull-out Capacity (if provided)
    """
    step = 0.05
    current_span = 0.5
    history = []
    
    valid_span = 0.5
    final_fem = None
    
    limit_reached = False
    
    while current_span <= max_span:
        fem = solve_continuous_beam_exact(current_span, num_spans, w_load)
        
        m_star = fem['max_moment']
        r_star = fem['rxn_max']
        
        # Check 1: Rail
        rail_util = (m_star / Mn) * 100
        rail_ok = m_star <= Mn
        
        # Check 2: Clamp
        clamp_util = 0.0
        clamp_ok = True
        if clamp_capacity is not None and clamp_capacity > 0:
            clamp_util = (r_star / clamp_capacity) * 100
            clamp_ok = r_star <= clamp_capacity
            
        status = "OK"
        fail_mode = "-"
        if not rail_ok:
            status = "Fail"
            fail_mode = "Rail Bending"
        elif not clamp_ok:
            status = "Fail"
            fail_mode = "Clamp Pull-out"
            
        history.append({
            'span': current_span,
            'm_star': m_star,
            'r_star': r_star,
            'util_rail': rail_util,
            'util_clamp': clamp_util,
            'status': status,
            'fail_mode': fail_mode
        })
        
        if rail_ok and clamp_ok:
            valid_span = current_span
            final_fem = fem
        else:
            limit_reached = True
            break
            
        current_span += step
        
    if final_fem is None:
        final_fem = solve_continuous_beam_exact(0.5, num_spans, w_load)
        valid_span = 0.5

    return valid_span, final_fem, history
