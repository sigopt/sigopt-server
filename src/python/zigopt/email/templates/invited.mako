<div>
  % if title is not None:
    <h1>${title}</h1>
  % endif
  <p>${inviter} has invited you to join the ${organization_name} organization on ${product_name} to collaborate on the following teams:</p>
  <ul>
    % for c in clients:
      <li>${c.name}</li>
    % endfor
  </ul>
  <p>Please create an account by clicking the Sign Up button below.</p>
  <a
      href="${link}"
      class="btn block"
      target="_blank" rel="noopener noreferrer">
    Sign Up
  </a>
  <p>
    ${sign_off}<br/>
    ${team_name}
  </p>
</div>
