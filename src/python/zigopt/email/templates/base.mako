## NOTE: This has a lot of pretty messy CSS, with lots of styles inlined.
## This has historically been a necessity in order to get the styles rendering
## as expected in most email clients, which are typically pretty conservative in
## what they allow
<%!
  import datetime
  def year():
    return datetime.date.today().year or 2021
%>
<!DOCTYPE html>
<html style="height: 100%;">
  <head>
    <style type="text/css">
      a {
        color: #245EAB;
        text-decoration: none;
        font-weight: 500;
      }
      a:hover {
        text-decoration: underline;
      }
      .btn {
        background-color: #15407D;
        padding: 8px 16px;
        border-radius:5px;
        font-size: 16px;
        color: #fff;
      }
      .btn.block {
        color: #fff;
        display: block;
        width: 20%;
        width: fit-content; /* overwrite in case supported */
        text-align: center;
      }
      ul {
        padding: 0 0 10px 40px;
      }
      h1 {
        font-weight: normal;
        color: #15407D;
      }
      /* MOBILE STYLES */
      @media screen and (max-width: 600px) {
        .img-max {
          width: 100% !important;
          max-width: 100% !important;
          height: auto !important;
        }
        .max-width {
          max-width: 100% !important;
        }
        .mobile-padding {
          padding-left: 5% !important;
          padding-right: 5% !important;
        }
      }
    </style>
  </head>
  <body style="margin: 0 0 0 0; height: 100%; background-color: #F9F9F9;">
    <div marginheight="10" marginwidth="10" style="padding-top: 50px; padding-bottom: 20px;" class="mobile-padding">
      <table border="0" align="center" cellpadding="0" cellspacing="0" style="font-family:Helvetica,Arial,sans-serif;border:1px solid #E5E5E5; max-width: 800px; width: 100%;">
        <tbody>
          <tr>
            <td align="left">
              <table align="center" border="0" cellspacing="0" cellpadding="0" bgcolor="#FFFFFF" style="width: 100%;">
                <tbody>
                <tr style="background:#0B3267 linear-gradient(to right, #0098d1, #245eab); height: 120px;">
                    <td align="middle" style="padding:8px 20px">
                      <a href="${app_url}" target="_blank" rel="noopener noreferrer"><img
                        src="${app_url}/static/img/SigOpt_logo_horiz_W.png" width="164" height="35" align="middle" alt="SigOpt"/></a>
                      <br>
                    </td>
                  </tr>
                </tbody>
              </table>
              <table align="center" border="0" cellspacing="0" cellpadding="0" bgcolor="#FFFFFF" style="width: 100%;" class="content">
                <tbody>
                  <tr>
                    <td valign="top" style="font-size:16px;line-height:24px;">
                      <table align="center" border="0" cellspacing="0" cellpadding="0" bgcolor="#FFFFFF" style="width: 100%;">
                        <tbody>
                          <tr>
                            <td style="padding:20px 20px;font-family:Helvetica,Arial,sans-serif;">
                              ${email_body | n}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </td>
                  </tr>
                </tbody>
              </table>
              <table border="0" cellspacing="0" cellpadding="0" style="width: 100%;">
                <tbody>
                  <tr>
                    <td bgcolor="#FFFFFF" valign="top" align="center" style="width: 100%;">
                      <div style="font-size:12px;color:#343740;margin-top:0;padding:0 0 4px 0;width:100%;border-top:1px solid #E6EAEC">
                        <p style="margin:14px 0 8px 0;padding:0;font-size:12px;">
                          <span>
                            <a href="https://twitter.com/sigopt" target="_blank" rel="noopener noreferrer"><img class="social" src="${app_url}/static/img/iconfinder_5296516_twitter.png" alt="Twitter" width="24" height="24" border="0"/></a>&nbsp;
                            <a href="https://github.com/sigopt" target="_blank" rel="noopener noreferrer"><img class="social" src="${app_url}/static/img/iconfinder_211904_github.png" alt="Github" width="24" height="24" border="0"/></a>&nbsp;
                            <a href="https://www.linkedin.com/company/sigopt" target="_blank" rel="noopener noreferrer"><img class="social" src="${app_url}/static/img/iconfinder_104493_linkedin.png" alt="LinkedIn" width="24" height="24" border="0"/></a>
                          </span>
                        </p>
                        <p style="margin:0 0 14px 0;padding:0;font-size:12px;margin-top:12px;font-family:Helvetica,Arial,sans-serif;line-height:1.5;">
                          <a href="[unsubscribe]" style="color:#0B3267;">Unsubscribe</a> from future emails.<br/>
                          SigOpt, Inc. 100 Bush St, Suite 1100. San Francisco, CA, 94104<br/>
                          Copyright 2014-${year()} SigOpt, Inc. All rights reserved
                        </p>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </body>
</html>
