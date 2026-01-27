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
    # Equation: M(i-1) + 4M(i) + M(i+1) = -wL^2/2
    # Boundary conditions: M(0) = 0, M(n) = 0 (Simple supports at ends)
    
    if num_spans == 1:
        M_supports = np.array([0.0, 0.0])
    else:
        # Number of internal supports
        n_internal = num_spans - 1
        
        # Build Matrix A
        A = np.zeros((n_internal, n_internal))
        for i in range(n_internal):
            A[i, i] = 4.0
            if i > 0: A[i, i-1] = 1.0
            if i < n_internal - 1: A[i, i+1] = 1.0
            
        # Build Matrix B
        B = np.full(n_internal, -0.5 * w * L**2)
        
        # Solve for Internal Moments
        if n_internal > 0:
            M_internal = np.linalg.solve(A, B)
            M_supports = np.concatenate(([0], M_internal, [0]))
        else:
            M_supports = np.zeros(n_supports)

    # 2. Calculate Reactions (R) from Support Moments
    # Take moments about each support to find shears
    R = np.zeros(n_supports)
    
    # Calculate Shear forces just to left and right of supports
    V_right = np.zeros(num_spans) # V at left of span i
    V_left = np.zeros(num_spans)  # V at right of span i
    
    for i in range(num_spans):
        # Moment equilibrium on free body of span i
        # Sum M about right end = 0 -> V_right*L - wL^2/2 + M_left - M_right = 0
        V_right[i] = (w * L**2 / 2 - M_supports[i] + M_supports[i+1]) / L
        # Sum Fy = 0
        V_left[i] = w * L - V_right[i] # Acting downwards relative to support, but let's calc R directly
        
    # Assemble Reactions
    R[0] = V_right[0]
    R[-1] = V_left[-1]
    for i in range(1, num_spans):
        R[i] = V_left[i-1] + V_right[i]

    # 3. Generate Plotting Data (High Resolution)
    # We slice each span into points
    points_per_span = 50
    total_points = points_per_span * num_spans
    x_plot = []
    shear_plot = []
    moment_plot = []
    
    for i in range(num_spans):
        x_local = np.linspace(0, L, points_per_span)
        # Shear V(x) = V_start - w*x
        v_local = V_right[i] - w * x_local
        # Moment M(x) = M_start + V_start*x - w*x^2/2
        m_local = M_supports[i] + V_right[i] * x_local - (w * x_local**2) / 2
        
        x_global = x_local + i * L
        
        x_plot.extend(x_global)
        shear_plot.extend(v_local)
        moment_plot.extend(m_local)

    return {
        'max_moment': np.max(np.abs(moment_plot)), # Use absolute max moment
        'moment_array': np.array(moment_plot),
        'shear_array': np.array(shear_plot),
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
        # Run exact analysis
        fem = solve_continuous_beam_exact(current_span, num_spans, w_load)
        
        m_star = fem['max_moment']
        r_star = fem['rxn_max']
        
        # --- Check 1: Rail Capacity ---
        rail_util = (m_star / Mn) * 100
        rail_ok = m_star <= Mn
        
        # --- Check 2: Clamp Capacity ---
        clamp_util = 0.0
        clamp_ok = True
        if clamp_capacity is not None and clamp_capacity > 0:
            clamp_util = (r_star / clamp_capacity) * 100
            clamp_ok = r_star <= clamp_capacity
            
        # Determine Status
        status = "OK"
        failure_mode = "-"
        
        if not rail_ok:
            status = "Fail"
            failure_mode = "Rail Bending"
        elif not clamp_ok:
            status = "Fail"
            failure_mode = "Clamp Pull-out"
            
        # Log History
        history.append({
            'span': current_span,
            'm_star': m_star,
            'r_star': r_star,
            'util_rail': rail_util,
            'util_clamp': clamp_util,
            'status': status,
            'fail_mode': failure_mode
        })
        
        if rail_ok and clamp_ok:
            valid_span = current_span
            final_fem = fem
        else:
            limit_reached = True
            break # Stop immediately when fail
            
        current_span += step
        
    # If inputs are weird and fail on first step, run analysis on min span to prevent None return
    if final_fem is None:
        final_fem = solve_continuous_beam_exact(0.5, num_spans, w_load)
        valid_span = 0.5

    return valid_span, final_fem, history
