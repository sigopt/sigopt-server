<div>
  % if title is not None:
    <h1>${title}</h1>
  % endif
  <p>With ${product_name} you can easily track runs, visualize training, and scale hyperparameter optimization for any model, library, and infrastructure.</p>
  <p>Visit your account now:</p>
  <a
      href="${app_url}"
      class="btn block"
      target="_blank" rel="noopener noreferrer">
    Login to ${product_name}
  </a>
  <p>Here are a few easy ways you can explore ${product_name} to get started:</p>
  <ul>
    <li style="margin-bottom: 5px;">
      <a
          href="https://colab.research.google.com/github/sigopt/sigopt-examples/blob/b73b2332a1975291267c417cd2c070555ea66d86/get-started/sigopt_experiment_and_optimization_demo.ipynb"
          target="_blank">
        Demo Notebook.
      </a> This quick notebook will guide you through how to integrate ${product_name} and start your first optimization experiment in just a few lines of code.
    </li>
    <li style="margin-bottom: 5px;">
      Tutorials. When in doubt, check out our
      <a
        href="${app_url}/docs/tutorial/experiment"
        target="_blank">
        Get Started Tutorial
      </a> and documentation for answers to your questions.
    </li>
    <li style="margin-bottom: 5px;">
      <a
        href="${app_url}/gallery"
        target="_blank">
        Code Examples.
      </a> Hit the ground running with starter code to help integrate ${product_name} into many different machine learning and deep learning frameworks.
    </li>
    <li style="margin-bottom: 5px;">
      <a
        href="https://sigopt.com/blog"
        target="_blank">
        Blog.
      </a> Our blog is the best source of information on product releases and research that will impact your ability to get the most out of your modeling.
    </li>
  </ul>
  <p>
    ${sign_off}<br/>
    ${team_name}
  </p>
</div>
