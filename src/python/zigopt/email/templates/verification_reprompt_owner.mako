<div>
  <p>
    % if user_name is not None:
      Hi ${user_name},
    % else:
      Welcome,
    % endif
  </p>
  <p>
    You have been invited to join the <b>${organization_name}</b> organization on ${product_name} as an owner.
    As an owner you will have full access to all teams within the organization, as well as the ability to view
    organization-level information.
  </p>
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
