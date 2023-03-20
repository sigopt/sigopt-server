<div>
  <p>
    % if user_name is not None:
      Hi ${user_name},
    % else:
      Welcome,
    % endif
  </p>
  <p>You have been invited to join the ${organization_name} ${product_name} organization on the following teams:</p>
  <ul>
    % for c in clients:
      <li>${c.name}</li>
    % endfor
  </ul>
  <a
      href="${link}"
      class="btn block"
      target="_blank" rel="noopener noreferrer">
    Verify Email
  </a>
  <p>
    ${sign_off}<br/>
    ${team_name}
  </p>
</div>
