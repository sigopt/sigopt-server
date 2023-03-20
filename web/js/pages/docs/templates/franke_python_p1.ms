import sigopt

sigopt.set_project({{& projectId}})

experiment = sigopt.create_experiment(
  name='Franke Optimization (Python)',
  # Define which parameters you would like to tune
  parameters=[
    dict(name='x', type='double', bounds=dict(min=0.0, max=1.0)),
    dict(name='y', type='double', bounds=dict(min=0.0, max=1.0)),
  ],
  metrics=[dict(name='function_value', objective='maximize')],
  parallel_bandwidth=1,
  # Define a budget for your experiment
  budget=30,
)
print("Created experiment: {{appUrl}}/experiment/" + experiment.id)
