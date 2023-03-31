Sys.setenv(SIGOPT_API_TOKEN="{{& apiToken}}")
{{#apiUrl}}
Sys.setenv(SIGOPT_API_URL="{{apiUrl}}")
{{/apiUrl}}

install.packages("SigOptR", repos = "http://cran.us.r-project.org")
library(SigOptR)
