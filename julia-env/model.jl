using Gen

@gen function sample_point(freq::Float64,
        fs::Vector{Float64},
        vs::Vector{Float64},
        params::Dict)

    g = freq*params["alpha_f"] + params["beta_f"]
    value = freq*params["alpha_v"] + params["beta_v"]
    epsilon = 4.0
    for (idx,freq) in enumerate(fs)
        if abs(freq-g) < epsilon
            value += vs[idx]*params["gamma_v"]
        end
    end
    return value
end

@gen function get_bin_borders(minf::Float64, maxf::Float64)
    num_bins = @addr(poisson(3), :n_bins)
    bin_borders = Vector{Float64}(undef,num_bins+1)
    offset = 0
    for b in 1:num_bins
        distance = @addr(uniform(0, maxf-offset), :bin_end => b)
        bin_borders[b] = distance+offset
        offset += distance
     end
     bin_borders[num_bins+1] = maxf
     return bin_borders
end

@gen function get_params()
    paramd = Dict()
    # g = alpha_f*q + beta_f
    paramd["alpha_f"] = @addr(normal(0,1), :alpha_f)
    paramd["beta_f"] = @addr(normal(0,1), :beta_f)
    # beta + gamma_v*q + alpha_v*(sum of signal values)
    paramd["beta_v"] = @addr(normal(0,1), :beta_v)
    paramd["alpha_v"] = @addr(normal(0,1), :alpha_v)
    paramd["gamma_v"] = @addr(normal(0,1), :gamma_v)
    return paramd
end

@gen function gen_model(maxf::Float64)
    # vector of bin borders (float64)
    borders = get_bin_borders(0.0,maxf)
    last_border = 0
    params = Dict()
    for (idx,border) in enumerate(borders)
        l = last_border
        u = border
        # returns dictionary of parameter distributions
        mu_pars = @addr(get_params(), idx => :mu_par)
        var_pars = @addr(get_params(), idx => :var_par)
        params[idx] = (l,u,mu_pars,var_pars)
        last_border = u
    end
    return params
end

@gen function sample_model(fs::Vector{Float64},
                    vs::Vector{Float64},
                    qs::Vector{Float64},
                    params::Dict)

    results = Vector{Float64}(undef,length(qs))
    for pdict_id in keys(params)
        (l,u,mu_pars,var_pars) = params[pdict_id]
        for (i, q) in enumerate(qs)
            if l <= q <= u
               mu = sample_point(q,fs,vs,mu_pars)
               var = sample_point(q,fs,vs,var_pars)
               results[i] = @addr(normal(mu,var), i => :noise)
            end
        end
    end
    return results
end

#########################
# inference operators   #
#########################

@gen function do_inference(n):
end

model = gen_model(500000.)
println(model)
fs = [0.,10.,20.,1000.]
xs = [0.5,0.1,0.1,0.2]
qs = Vector{Float64}(1:100)
#result = sample_model(fs,xs,qs)
#println(result)
observations = DynamicAssignment()
(trace, score) = generate(sample_model, (fs,xs,qs,model), observations)

assignment = get_assignment(trace)
println(score)
println(assignment)