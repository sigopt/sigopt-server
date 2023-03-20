<div>
  <p>
      % if user_name is not None:
        Hi ${user_name},
      % else:
        Welcome,
      % endif
  </p>
  <p>
      Thanks for choosing ${product_name}! Please confirm that
      you want to use this email address as
      your ${product_name} account email address.
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
