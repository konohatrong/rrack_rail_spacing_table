import numpy as np

def calculate_Mn(breaking_load_kN, test_span_m, safety_factor=1.0):
    M_failure = (breaking_load_kN * test_span_m) / 4.0
    Mn = M_failure / safety_factor
    return Mn

def solve_continuous_beam_fem(num_spans, span_length, w_load):
    """
    Returns:
        dict: {
            'max_moment': float,
            'x_vals': array,
            'shear_vals': array,
            'moment_vals': array,
            'reactions': list
        }
    """
    n_nodes = num_spans + 1
    n_dof = n_nodes * 2 
    
    K_global = np.zeros((n_dof, n_dof))
    F_global = np.zeros(n_dof)
    
    E = 1.0 
    I = 1.0 
    L = span_length
    
    # Stiffness matrix elements
    k11 = 12*E*I/L**3
    k12 = 6*E*I/L**2
    k22 = 4*E*I/L
    
    # Fixed End Forces
    fem_moment = w_load * L**2 / 12
    fem_shear = w_load * L / 2
    
    # Assembly
    for i in range(num_spans):
        # Nodes i and i+1
        # DOFs: 2*i, 2*i+1, 2*i+2, 2*i+3
        idx = [2*i, 2*i+1, 2*i+2, 2*i+3]
        
        # Local K
        k_local = np.array([
            [k11, k12, -k11, k12],
            [k12, k22, -k12, k22/2],
            [-k11, -k12, k11, -k12],
            [k12, k22/2, -k12, k22]
        ])
        
        # Local F (Fixed End Forces)
        f_local = np.array([fem_shear, fem_moment, fem_shear, -fem_moment])
        
        # Add to Global
        for r in range(4):
            F_global[idx[r]] += f_local[r]
            for c in range(4):
                K_global[idx[r], idx[c]] += k_local[r, c]

    # Boundary Conditions: Fix all vertical displacements (0, 2, 4...)
    fixed_dofs = [2*i for i in range(n_nodes)]
    free_dofs = [i for i in range(n_dof) if i not in fixed_dofs]
    
    # Solve for rotations
    K_reduced = K_global[np.ix_(free_dofs, free_dofs)]
    F_effective = -F_global[free_dofs] # Load vector = - Fixed End Actions (since nodal loads are 0)
    
    displacements = np.linalg.solve(K_reduced, F_effective)
    
    u_full = np.zeros(n_dof)
    u_full[free_dofs] = displacements
    
    # --- Post Processing for Plotting ---
    x_total = []
    shear_total = []
    moment_total = []
    max_moment = 0.0
    reactions = np.zeros(n_nodes)
    
    # Calculate Reactions: R = K*u + F_fixed_actions
    # We need to rebuild F_fixed_actions vector globally to add to K*u
    F_fixed_global = np.zeros(n_dof)
    for i in range(num_spans):
        idx = [2*i, 2*i+1, 2*i+2, 2*i+3]
        f_local = np.array([fem_shear, fem_moment, fem_shear, -fem_moment])
        for r in range(4):
            F_fixed_global[idx[r]] += f_local[r]
            
    forces_global = np.dot(K_global, u_full) + F_fixed_global
    
    # Extract vertical reactions (odd indices: 0, 2, 4...)
    for i in range(n_nodes):
        reactions[i] = forces_global[2*i]

    # Discretize for plotting
    points_per_span = 50
    
    for i in range(num_spans):
        # Element displacements
        idx = [2*i, 2*i+1, 2*i+2, 2*i+3]
        u_ele = u_full[idx]
        
        # Start and End forces of member from slope deflection eq
        # Note: We need internal forces at distance x.
        # Simple beam theory superposition:
        # M(x) = M_start*(1-x/L) + M_end*(x/L) + M_simple(x) ... messy with Hermitian.
        # Easier: M(x) = EI * d2v/dx2.
        # But even easier for Uniform Load:
        # Calculate Member End Moments from K_local * u_ele + f_local
        k_local = np.array([
            [k11, k12, -k11, k12],
            [k12, k22, -k12, k22/2],
            [-k11, -k12, k11, -k12],
            [k12, k22/2, -k12, k22]
        ])
        f_local = np.array([fem_shear, fem_moment, fem_shear, -fem_moment])
        f_int = np.dot(k_local, u_ele) + f_local
        
        V_start = f_int[0]
        M_start = f_int[1] # Counter-clockwise positive
        
        # Generate points
        x_local = np.linspace(0, L, points_per_span)
        
        # Mechanics Sign Convention for Beam (Sagging +, Hogging -)
        # Structural Analysis Matrix usually: Anti-clockwise moments +
        # We need to convert to standard beam diagrams.
        # Shear V(x) = V_start - w*x
        # Moment M(x) = -M_start + V_start*x - w*x^2/2 (Assuming M_start is CCW acting on beam end)
        
        # Note on M_start sign from Matrix method:
        # If matrix result is +ve, it is CCW.
        # On the left end of a beam, CCW moment creates Hogging (Negative Moment).
        # So Beam Moment = - (Matrix Moment)
        
        v_vals = V_start - w_load * x_local
        m_vals = -M_start + V_start * x_local - (w_load * x_local**2)/2
        
        x_global = x_local + (i * L)
        
        x_total.extend(x_global)
        shear_total.extend(v_vals)
        moment_total.extend(m_vals)
        
        max_moment = max(max_moment, np.max(np.abs(m_vals)))

    return {
        'max_moment': max_moment,
        'x': np.array(x_total),
        'shear': np.array(shear_total),
        'moment': np.array(moment_total),
        'reactions': reactions
    }

def optimize_span(Mn, w_load, num_spans, start_span=0.5, step=0.05, max_span=4.0):
    valid_span = start_span
    last_result = None
    
    for span in np.arange(start_span, max_span + step, step):
        res = solve_continuous_beam_fem(num_spans, span, w_load)
        if res['max_moment'] < Mn:
            valid_span = span
            last_result = res
        else:
            break
    
    # Re-run strictly for the valid span to get exact plot data if loop broke early
    final_res = solve_continuous_beam_fem(num_spans, valid_span, w_load)
    return valid_span, final_res