<div>
  <p>${inviter} has invited you to join the ${organization_name} ${product_name} organization on the following teams:</p>
  <ul>
    % for c in clients:
      <li>${c.name}</li>
    % endfor
  </ul>
  <a
      href="${link}"
      class="btn block"
      target="_blank" rel="noopener noreferrer">
    Check It Out
  </a>
  <p>
    ${sign_off}<br/>
    ${team_name}
  </p>
</div>
