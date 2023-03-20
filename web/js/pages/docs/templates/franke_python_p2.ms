# Evaluate your model with the suggested parameter assignments
# Franke function - http://www.sfu.ca/~ssurjano/franke2d.html
def evaluate_model(params):
  return franke_function(params['x'], params['y'])

# Run the Optimization Loop
for run in experiment.loop():
  with run:
    value = evaluate_model(run.params)
    run.log_metric("function_value", value)

# Fetch the best configuration and explore your experiment
best_run = next(experiment.get_best_runs())
best_assignments = best_run.assignments
print("Best Assignments: " + str(best_assignments))
print("Best x value: " + str(best_assignments['x']))
print("Best y value: " + str(best_assignments['y']))
print("Explore your experiment: {{appUrl}}/experiment/" + experiment.id + "/analysis")
