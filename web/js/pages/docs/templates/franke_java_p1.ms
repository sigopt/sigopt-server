// See https://github.com/sigopt/sigopt-java for installation instructions
import com.sigopt.Sigopt;
import com.sigopt.example.Franke;
import com.sigopt.model.Assignments;
import com.sigopt.model.Bounds;
import com.sigopt.model.Experiment;
import com.sigopt.model.Observation;
import com.sigopt.model.Parameter;
import com.sigopt.model.Suggestion;
import java.util.Arrays;

Sigopt.clientToken = {{& apiToken }};
{{#apiUrl}}
Sigopt.setApiBase("{{apiUrl}}");
{{/apiUrl}}

Experiment experiment = Experiment.create().data(new Experiment.Builder()
  .name("Franke Optimization (Java)")
  // Define which parameters you would like to tune
  .parameters(Arrays.asList(
    new Parameter.Builder().name("x").bounds(new Bounds(0.0, 1.0)).type("double").build(),
    new Parameter.Builder().name("y").bounds(new Bounds(0.0, 1.0)).type("double").build()
  ))
  .metrics(Arrays.asList(
    new Metric.Builder()
      .name("function_value")
      .build()
    ))
  .parallelBandwidth(1)
  // Define an Observation Budget for your experiment
  .observationBudget(30)
  .project({{& projectId}})
  .build())
  .call();
System.out.println("Created experiment: {{appUrl}}/experiment/" + experiment.getId());

