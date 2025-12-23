import numpy as np

def calculate_Mn(breaking_load_kN, test_span_m, safety_factor=1.0):
    M_failure = (breaking_load_kN * test_span_m) / 4.0
    Mn = M_failure / safety_factor
    return Mn

def solve_continuous_beam_fem(num_spans, span_length, w_load):
    """
    Analyzes a continuous beam using Matrix Stiffness Method.
    Returns detailed dictionary including separated reactions.
    """
    n_nodes = num_spans + 1
    n_dof = n_nodes * 2 
    
    K_global = np.zeros((n_dof, n_dof))
    F_global = np.zeros(n_dof)
    
    E = 1.0; I = 1.0; L = span_length
    
    # Stiffness matrix elements
    k11 = 12*E*I/L**3; k12 = 6*E*I/L**2; k22 = 4*E*I/L
    
    # Fixed End Forces (Uniform Load)
    fem_moment = w_load * L**2 / 12
    fem_shear = w_load * L / 2
    
    for i in range(num_spans):
        idx = [2*i, 2*i+1, 2*i+2, 2*i+3]
        k_local = np.array([
            [k11, k12, -k11, k12], [k12, k22, -k12, k22/2],
            [-k11, -k12, k11, -k12], [k12, k22/2, -k12, k22]
        ])
        f_local = np.array([fem_shear, fem_moment, fem_shear, -fem_moment])
        
        for r in range(4):
            F_global[idx[r]] += f_local[r]
            for c in range(4):
                K_global[idx[r], idx[c]] += k_local[r, c]

    fixed_dofs = [2*i for i in range(n_nodes)] # Fix vertical displacements
    free_dofs = [i for i in range(n_dof) if i not in fixed_dofs]
    
    K_reduced = K_global[np.ix_(free_dofs, free_dofs)]
    F_effective = -F_global[free_dofs]
    
    displacements = np.linalg.solve(K_reduced, F_effective)
    u_full = np.zeros(n_dof)
    u_full[free_dofs] = displacements
    
    # Post-processing
    x_total = []; shear_total = []; moment_total = []
    max_moment = 0.0
    reactions = np.zeros(n_nodes)
    
    # Calculate Reactions (R = K*u + F_fixed)
    F_fixed_global = np.zeros(n_dof)
    for i in range(num_spans):
        idx = [2*i, 2*i+1, 2*i+2, 2*i+3]
        f_local = np.array([fem_shear, fem_moment, fem_shear, -fem_moment])
        for r in range(4): F_fixed_global[idx[r]] += f_local[r]
            
    forces_global = np.dot(K_global, u_full) + F_fixed_global
    for i in range(n_nodes): reactions[i] = forces_global[2*i]

    # Plotting data points
    points_per_span = 50
    for i in range(num_spans):
        idx = [2*i, 2*i+1, 2*i+2, 2*i+3]
        u_ele = u_full[idx]
        
        k_local = np.array([[k11, k12, -k11, k12], [k12, k22, -k12, k22/2], [-k11, -k12, k11, -k12], [k12, k22/2, -k12, k22]])
        f_local = np.array([fem_shear, fem_moment, fem_shear, -fem_moment])
        f_int = np.dot(k_local, u_ele) + f_local
        
        V_start = f_int[0]; M_start = f_int[1]
        x_local = np.linspace(0, L, points_per_span)
        
        v_vals = V_start - w_load * x_local
        m_vals = -M_start + V_start * x_local - (w_load * x_local**2)/2
        
        x_total.extend(x_local + (i * L))
        shear_total.extend(v_vals)
        moment_total.extend(m_vals)
        max_moment = max(max_moment, np.max(np.abs(m_vals)))

    # --- Separate Edge vs Internal Reactions ---
    abs_reactions = np.abs(reactions)
    rxn_edge = max(abs_reactions[0], abs_reactions[-1]) # Max of first or last support
    
    if n_nodes > 2:
        rxn_internal = np.max(abs_reactions[1:-1]) # Max of any middle support
    else:
        rxn_internal = 0.0 # Single span case

    return {
        'max_moment': max_moment,
        'x': np.array(x_total),
        'shear': np.array(shear_total),
        'moment': np.array(moment_total),
        'reactions': reactions,
        'rxn_edge': rxn_edge,
        'rxn_internal': rxn_internal
    }

def optimize_span(Mn, w_load, num_spans, start_span=0.5, step=0.05, max_span=4.0):
    valid_span = start_span
    last_result = None
    history = []
    
    for span in np.arange(start_span, max_span + step, step):
        res = solve_continuous_beam_fem(num_spans, span, w_load)
        m_star = res['max_moment']
        util = (m_star / Mn) * 100
        status = "OK" if m_star <= Mn else "FAIL"
        
        history.append({
            'span': float(span), 'm_star': float(m_star), 'util': float(util), 'status': status
        })
        
        if m_star <= Mn:
            valid_span = span
            last_result = res
        else:
            break
            
    if last_result is None: # Safety fallback
        last_result = solve_continuous_beam_fem(num_spans, valid_span, w_load)
        
    return valid_span, last_result, history
