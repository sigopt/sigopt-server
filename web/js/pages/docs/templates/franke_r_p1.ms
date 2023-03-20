install.packages("devtools", repos = "http://cran.us.r-project.org")
library(devtools)
install_github("sigopt/SigOptR")
library(SigOptR)
Sys.setenv(SIGOPT_API_TOKEN={{& apiToken }})
{{#apiUrl}}
Sys.setenv(SIGOPT_API_URL="{{apiUrl}}")
{{/apiUrl}}


experiment <- create_experiment(list(
  name="Franke Optimization (R)",
  # Define which parameters you would like to tune
  parameters=list(
    list(name="x", type="double", bounds=list(min=0.0, max=1.0)),
    list(name="y", type="double", bounds=list(min=0.0, max=1.0))
  ),
  metrics=list(
  	list(name="function_value")
  ),
  parallel_bandwidth=1,
  # Define an Observation Budget for your experiment
  observation_budget=30,
  project={{& projectId}}
))
print(paste(
  "Created experiment: {{appUrl}}/experiment",
  experiment$id,
  sep="/"
))
