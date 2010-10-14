<?php
// $Id: shib_auth.module,v 1.3.4.5.2.31 2009/09/30 17:00:49 bajnokk Exp $
/**
 * @file
 * This is a Shibboleth authentication module.
 *
 * This module allow administrators to enable Shibboleth based authentication on their drupal installation.
 */

/**
 * Display help and module information
 * @param path which path of the site we're displaying help
 * @param arg array that holds the current path as would be returned from arg() function
 * @return help text for the path
 */
function shib_auth_help($path, $arg) {
  $output = '';
  switch ($path) {
    case 'admin/help#shib_auth':
      //TODO
      $output ='<p>'. t("The Shibboleth authentication module lets you utilize the advantages of the Single Sign On (SSO) methods.") .'</p>';
      $output .='<p>'. t("For more help related to Shibboleth and module configuration, see <a href=\"@wiki\">NIIF AAI wiki pages</a>.",
      array('@wiki' => url('https://wiki.aai.niif.hu/index.php/Drupal_Shibboleth_module'))) .'</p>';

      break;
    case 'admin/user/shib_auth':
      $output = '<p>'. t("The text shown in the block and on other login pages can be changed on the <a href=\"@block\">block settings page</a>.",
        array('@block' => url('admin/build/block/configure/shib_auth/0'))) .'</p>';
      break;
  }
  return $output;
} // function shib_auth_help

function shib_auth_isDebug() {
  return variable_get('shib_auth_debug_state', FALSE) &&
        drupal_substr($_GET['q'], 0, drupal_strlen(variable_get('shib_auth_debug_url', ''))) == variable_get('shib_auth_debug_url', '');
}

/**
 * Create a new user based on informations from the Shibboleth handler if it's necessary or log in.
 *
 * If already authenticated - do nothing
 * If Shibboleth doesn't provide User information - error message
 * Else if user exists, and mail override (shib_auth_req_shib_only) enabled, override existing user info
 * If not exists, and Shibboleth provides mail address, create an account for this user
 * If there's no mail attribute, ask for the mail address on a generated form if mail override (shib_auth_req_shib_only) is disabled
 * In this case, the account will be created with this e-mail address.
 *
 * This function also gives roles to the user, if certain server fields were provided by the Shibboleth server
 */
function shib_auth_init() {
  global $user;

  $shib_headers_exist = ($_SERVER['HTTP_SHIB_IDENTITY_PROVIDER'] || $_SERVER['Shib-Identity-Provider']);

  if (shib_auth_isDebug()) {
    $debug_message = print_r($_SERVER, TRUE);
    drupal_set_message('<pre>'. $debug_message .'</pre>');
  }

  // if the user IS logged in as non-admin, but we're missing Shibboleth identity
  if (!$shib_headers_exist && $_SESSION['authentication'] == 'shib_auth' &&
      variable_get('shib_auth_auto_destroy_session', FALSE) && $user->uid && $user->uid != 1) {
    drupal_set_message(t('Your session is expired. Please log in again!'), "error");
    unset($_SESSION['authentication']);
    session_destroy();
    $user = drupal_anonymous_user();
  }

  $uname = $_SERVER[variable_get('shib_auth_username_variable', 'REMOTE_USER')];
  $umail= $_SERVER[variable_get('shib_auth_username_email', 'HTTP_SHIB_MAIL')];
  $umail_single = preg_replace('/;.*/', '', $umail);

  // Ensure that the user is the same as the one who has initiated the session
  if (isset($_SESSION['uname'])) {
	  if ($_SESSION['uname'] != $uname) { 
		  unset($_SESSION['authentication']);
		  unset($_SESSION['uname']);
		  session_destroy();
		  $user = drupal_anonymous_user();
	  }
  } else {
	  $_SESSION['uname'] = $uname;
  }

  // If
  // - The user isn't logged in
  // - There is Shibboleth authentication in the background
  // - The settings are fine and there has been a valid username set up
  // - The settings are fine and there has been a valid user email address set up
  if (!$user->uid && $shib_headers_exist) {
    //If custom mail form will be generated, generate it only once
    if ( isset($_SESSION['redirected_to_custom_mail_form']) && $_SESSION['redirected_to_custom_mail_form']) {
      unset($_SESSION['redirected_to_custom_mail_form']);
    }

    else {
      //Shib didn't provide username, or the admin gave wrong server variable on the shib config form
      if (!$uname) {
        $message = t('Username is missing. Please contact your Shibboleth administrator!');
        drupal_set_message($message, "error");
        watchdog('shib_auth', $message, WATCHDOG_CRITICAL);
      }
      //The module got the username from shib
      else {
        $username_query = db_query("SELECT * FROM {users} WHERE name='%s'", $uname);
        $new_user = !db_fetch_object($username_query);
        //The user exists in the drupal user database, login her
        if (!$new_user) {
          user_external_login_register($uname, "shib_auth");
          $_SESSION['authentication'] = 'shib_auth';
          //if we have an e-mail address from the shib server
          if ($umail_single) {
            //and the Shibboleth mail address override was enabled in the admin config
            if (variable_get('shib_auth_mail_shib_only', 0)==0) {
            //check if there isn't any user with this e-mail (whose name is different)
              $email_for_other_user_query=
                          db_query("SELECT * FROM {users} WHERE mail='%s' AND name <> '%s'", $umail_single, $uname );
              $email_for_other_user = db_fetch_object($username_and_email_query);
              if ($email_for_other_user) {
                drupal_set_message(t("Error saving user account. E-mail address is already used."), 'error');
              }
              //if everything is allright, modify the mail address of the user.
              else {
                $user = user_save($user, array('mail' => $umail_single));
              }
            }
          }
        }
        else {
          //If we have an e-mail address from the shib server, and there isn't any user with this address, create an account with these infos
          if ($umail_single) {
            $email_already_used_query =
                    db_query("SELECT * FROM {users} WHERE mail='%s'", $umail_single );
            $email_already_used = db_fetch_object($email_already_used_query);
            // If the mail address is used, give an error
            if ($email_already_used) {
              drupal_set_message(t("Error saving user account. E-mail address is already used."), 'error');
            }
            else {
              user_external_login_register($uname, "shib_auth");
              $_SESSION['authentication'] = 'shib_auth';
              $user = user_save($user, array('mail' => $umail_single));
            }
          }
          //If the module didn't received mail address from shibboleth, it can't override the user's existing address
          else {
            if (variable_get('shib_auth_mail_shib_only', 0)==0) {
              $message = t('E-mail address is missing. Please contact your Shibboleth administrator!');
              drupal_set_message($message, "error");
              watchdog('shib_auth', $message, WATCHDOG_CRITICAL);
            }
            // if there's no override, the admin can enable users to provide their own e-mail address on an appropriate form
            else {
            // if the custom mail was enabled on the admin form
              
                if ($_POST['form_id'] == 'shib_auth_custom_email' && $_POST['custom_mail']) $custom_mail = $_POST['custom_mail'];
                //if the user provided the custom mail string, and it is not empty
                if (isset($custom_mail) && $custom_mail) {
                // and it isn't used by another registered drupal user
                  $email_already_used_query = db_query("SELECT * FROM {users} WHERE mail='%s'", $custom_mail);
                  $email_already_used = db_fetch_object($email_already_used_query);
                  if ($email_already_used) {
                    drupal_set_message(t("Error saving user account. E-mail address is already used."), 'error');
                  }
                  //register the user with the given address, and the shib provided username
                  else {
                    user_external_login_register($uname, "shib_auth");
                    $_SESSION['authentication'] = 'shib_auth';
                    $user = user_save($user, array('mail' => $custom_mail));
                  }
                  //then the user is redirected to the page, which she wanted to open before the auth process had been initiated
                  if (isset($_SESSION['redirected_to_custom_mail_form_url'])) {
                    $redirect_url = $_SESSION['redirected_to_custom_mail_form_url'];
                    unset($_SESSION['redirected_to_custom_mail_form_url']);
                    drupal_goto($redirect_url);
                  }
                }
                //We want to show the custom mail input form, and then redirect the user to the node, he wanted to go
                else {
                  $_SESSION['redirected_to_custom_mail_form'] = TRUE;
                  $_SESSION['redirected_to_custom_mail_form_url'] = $_GET['q'];
                  drupal_goto('shib_auth/get_custom_mail');
                }
              
            }
          }
        }
      }
    }
  }


  //The admin can define authorization rules based on the server variables - which are provided by Shibboleth -
  //to give roles to users, if the IdP provide certain authorization or authentication string
  //the rules can be defined as a server field - Regexp - role(s) trio

  // Store rules for further examination
  $former_rules = serialize($user->roles);

// Examine all previously saved rule
  $rules = db_query("SELECT * FROM {shib_auth}");
  while ($rule = db_fetch_array($rules)) {

    $fieldname = $rule['field'];
    $expression = '/'. urldecode($rule['regexpression']) .'/';
    //check out, if the given server field exists
    if (isset($_SERVER[$fieldname])) {
      foreach (explode(';', $_SERVER[$fieldname]) as $value) {
      //check if the RegEx can be fit to one of the value of the server field
        if (preg_match($expression, trim($value))) {
          $roles = unserialize(urldecode($rule['role']));
          //if there is a match, give this user the specified role(s)
          if (!empty($roles)) foreach ($roles as $key => $value) $user->roles[$key] = $value;
        }
      }
    }
  }
  $user->roles = array_filter($user->roles);

  // If the user roles array has been changed then reset the permission cache
  if (serialize($user->roles) != $former_rules) {
    // Hack to reset the permissions
    user_access('access content', $account, TRUE);
  }
} // function shib_auth_init()

/**
 * Let the user exit from the Shibboleth authority when he/she log out from the actual Drupal site.
 * @param op What kind of action is being performed.
 * @param edit The array of form values submitted by the user.
 * @param account The user object on which the operation is being performed.
 * @param category The active category of user information being edited.
 */
function shib_auth_user($op, &$edit, &$account, $category = NULL) {
  global $base_url, $user;

  if ($op == "logout") {
    $handlerurl = variable_get('shib_auth_handler_url', '/Shibboleth.sso');
    $handlerprotocol = variable_get('shib_auth_handler_protocol', 'https');
    if (ereg("^http[s]{0,1}://", $handlerurl) ) {
      // If handlerurl is an absolute path
      $logouthandler = $handlerurl ."/Logout";
    }
    else {
      // Else, if the handlerurl is a relative path
      // If the WAYF's URI doesn't start with slash then extend it
      if ( !ereg("^/", $handlerurl) ) $handlerurl = "/". $handlerurl;
      $logouthandler = $handlerprotocol ."://". $_SERVER['HTTP_HOST'] . $handlerurl ."/Logout";
    }
    unset($_SESSION['authentication']);
    $logout_redirect = variable_get('shib_logout_url', $base_url);
    // If the logout_redirect URL was relative extension is needed.
    if (!ereg("^http[s]{0,1}://", $logout_redirect) ) {
      $logout_redirect = $base_url .'/'. $logout_redirect;
    }
    drupal_goto("$logouthandler?return=$logout_redirect");
  }
  else if ($op == "delete") {
    db_query("DELETE FROM {authmap} WHERE uid = %d AND authname = '%s' AND module = 'shib_auth'",
            $account->uid, $account->name);
  }
} // function shib_auth_user(logout)

/**
 * Valid permissions for this module
 * @return array An array of valid permissions for the shib_auth module
 */

function shib_auth_perm() {
  return array('administer shibboleth authentication');
} // function shib_auth_perm()

/**
 * Generate the login text in HTML format using the 't' function
 * @returns HTML text of the login form
 */
function generate_login_text() {
  global $user;

  if (!$user->uid) {
    $handlerurl = variable_get('shib_auth_handler_url', '/Shibboleth.sso');
    $handlerprotocol = variable_get('shib_auth_handler_protocol', 'https');
    $wayfuri = variable_get('shib_auth_wayf_uri', '/DS');

    // If the WAYF's URI doesn't start with slash then extend it
    if ( !ereg("^/", $wayfuri) ) {
      $wayfuri = "/". $wayfuri;
    }

    $handler = '';
    $block_content = '';

    if (ereg("^http[s]{0,1}://", $handlerurl) ) {
      // If handlerurl is an absolute path
      $handler = $handlerurl . $wayfuri;
    }
    else {
      // Else, if the handlerurl is a relative path
      // If the WAYF's URI doesn't start with slash then extend it
      if ( !ereg("^/", $handlerurl) ) $handlerurl = "/". $handlerurl;
      $handler = $handlerprotocol ."://". $_SERVER['HTTP_HOST'] . $handlerurl . $wayfuri;
    }
    //Check whether clean url and i18 is enabled, and insert ?q=/ in the return url if not
    $url_prefix = '';
    if (!module_exists("i18n") && !variable_get('clean_url', FALSE)) {
      $url_prefix = '?q=';
    }
    //$actuallocation: the path where the Shibboleth should return
    $actuallocation = (isset($_SERVER['HTTPS']) ? 'https' : 'http') 
                             .'://'. $_SERVER['HTTP_HOST']
                             . url('<front>')
                             . $url_prefix
                             .'/shib_login/'
                             . $_GET['q'];
    // If there is no session yet then we should put the login text into the block
    $block_content .= "<p><b><a href=\"$handler?target=". urlencode($actuallocation) ."\">"
                   . variable_get('auth_link_text', t('Shibboleth Login'))
                   ."</a></b></p>";

    return $block_content;
  }
} // function generate_login_text()

/**
 * Generate the HTML text for the shib_auth login block
 * @param op the operation from the URL
 * @param delta offset
 * @returns block HTML
 */
function shib_auth_block($op='list', $delta=0, $edit = array()) {
  // listing of blocks, such as on the admin/block page
  switch ($op) {
    case "list":
      $blocks[0] = array(
        'info'       => t('Shibboleth authentication'),
        'status'     => TRUE,
        'visibility' => 1,
        'weight'     => 0,
        'region'     => 'left'
      );
      return $blocks;
    case 'configure':
      $form = array();
      switch ($delta) {
      case 0:
        $form['auth_link_text'] = array(
          '#type'          => 'textfield',
          '#title'         => t('Text of the auth link'),
          '#require'       => TRUE,
          '#size'          => 60,
          '#description'   => t('Here you can replace the text of the authentication link.'),
          '#default_value' => variable_get('auth_link_text', t('Shibboleth Login')),
        );
      }
      return $form;
    case 'save':
      switch ($delta) {
        case 0:
        variable_set('auth_link_text', $edit['auth_link_text']);
      }
      break;
    case "view": default:
      switch ($delta) {
        case 0:
          $block = array(
          'subject' => t('Shibboleth login'),
          'content' => generate_login_text() );
        break;
      }
      return $block;
  }
} // function shib_auth_block()

/**
 * Generate the administration form of the Shibboleth authentication module
 * @returns HTML text of the administration form
 */
function shib_auth_admin() {
  global $base_url;

  $form = array();

  $form['shib_handler_settings'] = array(
    '#type'        => 'fieldset',
    '#title'       => t('Shibboleth handler settings'),
    '#weight'      => 0,
    '#collapsible' => FALSE,
  );

  $form['shib_attribute_settings'] = array(
    '#type'        => 'fieldset',
    '#title'       => t('Attribute settings'),
    '#weight'      => 0,
    '#collapsible' => FALSE,
  );


  $form['shib_handler_settings']['shib_auth_handler_url'] = array(
    '#type'          => 'textfield',
    '#title'         => t('Shibboleth handler URL'),
    '#default_value' => variable_get('shib_auth_handler_url', '/Shibboleth.sso'),
    '#description'   => t('The URL can be absolute or relative to the server base url: http://www.example.com/Shibboleth.sso; /Shibboleth.sso'),
  );

  $form['shib_handler_settings']['shib_auth_handler_protocol'] = array(
    '#type'          => 'select',
    '#title'         => t('Shibboleth handler protocol'),
    '#default_value' => variable_get('shib_auth_handler_protocol', 'https'),
    '#options'       => array(
      'http'  => t('HTTP'),
      'https' => t('HTTPS'),
    ),
    '#description'   => t('This option will be effective only if the handler URL is a relative path.'),
  );

  $form['shib_handler_settings']['shib_auth_wayf_uri'] = array(
    '#type'          => 'textfield',
    '#title'         => t('WAYF location'),
    '#default_value' => variable_get('shib_auth_wayf_uri', '/DS'),
  );

  $form['shib_attribute_settings']['shib_auth_username_variable'] = array(
    '#type'          => 'textfield',
    '#title'         => t('Server variable for username'),
    '#default_value' => variable_get('shib_auth_username_variable', 'REMOTE_USER'),
  );

  $form['shib_attribute_settings']['shib_auth_username_email'] = array(
    '#type'          => 'textfield',
    '#title'         => t('Server variable for e-mail address'),
    '#default_value' => variable_get('shib_auth_username_email', 'HTTP_SHIB_MAIL'),
  );

  
  $form['shib_attribute_settings']['shib_auth_mail_shib_only'] = array(
    '#type' => 'radios',
    '#title' => t('E-mail source settings'),
    '#default_value' => variable_get('shib_auth_mail_shib_only', 0),
    '#options' => array(t('Require and use only Shibboleth-provided email address'), t('Ask for missing e-mail address')));

  $form['shib_attribute_debug'] = array(
    '#type'          => 'fieldset',
    '#title'         => 'Debugging options',
  );

  $form['shib_attribute_debug']['shib_auth_debug_state'] = array(
    '#type'          => 'checkbox',
    '#title'         => t('Enable DEBUG mode.'),
    '#default_value' => variable_get('shib_auth_debug_state', FALSE),
  );

  $form['shib_attribute_debug']['shib_auth_debug_url'] = array(
    '#type' => 'textfield',
    '#title'         => t('DEBUG path prefix'),
    '#default_value' => variable_get('shib_auth_debug_url', ''),
    '#description'   => t('For example use \'user/\' for display DEBUG messages on paths \'user/*\'!')
  );

  $form['shib_auth_auto_destroy_session']['shib_auth_auto_destroy_session'] = array(
    '#type'          => 'checkbox',
    '#title'         => t('Destroy Drupal session when the Shibboleth session expires.'),
    '#default_value' => variable_get('shib_auth_auto_destroy_session', FALSE),
  );

  $form['shib_logout_settings'] = array(
    '#type' => 'fieldset',
    '#title' => t('Change Logout settings'),
  );

  $form['shib_logout_settings']['shib_logout_url'] = array(
    '#type' => 'textfield',
    '#title' => t("URL to redirect to after logout"),
    '#default_value' => variable_get('shib_logout_url', $base_url),
    '#description' => t("The URL can be absolute or relative to the server base url. The relative paths will be automatically extended with the site base URL.")
  );

  return system_settings_form($form);
} // function shib_auth_admin()

/**
 * Generate the menu element to access the Shibboleth authentication module's administration page
 * @returns HTML text of the administer menu element
 */
function shib_auth_menu() {
  $items = array();

  $items['admin/user/shib_auth'] = array(
    'title'            => t('Shibboleth settings'),
    'description'      => t('Settings of the Shibboleth authentication module'),
    'page callback'    => 'drupal_get_form',
    'page arguments'   => array('shib_auth_admin'),
    'access arguments' => array('administer shibboleth authentication'),
  );

  $items['admin/user/shib_auth/general'] = array(
    'title'            => t('General settings'),
    'type'             => MENU_DEFAULT_LOCAL_TASK,
    'access arguments' => array('administer shibboleth authentication'),
    'weight'           => -10,
  );

  $items['admin/user/shib_auth/rules'] = array(
    'title'            => t('Shibboleth group rules'),
    'description'      => t('Administer attribute-based role assignment'),
    'page callback'    => '_shib_auth_list_rules',
    'page arguments'   => array('shib_auth_list_rules'),
    'access arguments' => array('administer permissions'),
    'type'             => MENU_LOCAL_TASK,
    'weight'           => -8,
  );

  $items['admin/user/shib_auth/new'] = array(
    'title'            => t('Add new rule'),
    'description'      => t('Add new attribute-based role assignment rule'),
    'page callback'    => 'drupal_get_form',
    'page arguments'   => array('shib_auth_new_rule'),
    'access arguments' => array('administer permissions'),
    'type'             => MENU_LOCAL_TASK,
    'weight'           => -7,
  );

  $items['admin/user/shib_auth/delete/%'] = array(
    'title'            => 'Delete rule',
    'page callback'    => '_shib_auth_delete_rule',
    'page arguments'   => array(4),
    'access arguments' => array('administer permissions'),
    'type'             => MENU_CALLBACK,
  );

  $items['admin/user/shib_auth/edit/%'] = array(
    'title'            => 'Edit rule',
    'page callback'    => 'drupal_get_form',
    'page arguments'   => array('shib_auth_edit_rule', 4),
    'access arguments' => array('administer permissions'),
    'type'             => MENU_NORMAL_ITEM,
  );

  $items['admin/user/shib_auth/clone/%'] = array(
    'title'            => 'Edit rule',
    'page callback'    => '_shib_auth_clone_rule',
    'page arguments'   => array(4),
    'access arguments' => array('administer permissions'),
    'type'             => MENU_CALLBACK,
  );

  $items['shib_auth/get_custom_mail'] = array(
    'title'            => t('Please enter your email address'),
    'page callback'    => 'drupal_get_form',
    'page arguments'   => array('shib_auth_custom_email'),
    'access arguments' => array('access content'),
    'type'             => MENU_CALLBACK,
  );

  $items['shib_login/%'] = array(
    'page callback'    => 'shib_login',
    'type'             => MENU_CALLBACK,
    'access callback'  => 'access_shib_login',
  );
  return $items;
} // function shib_auth_menu()
/**
 * This function prevents drupal loading a cached page after shibboleth login
 */
function shib_login() {
  drupal_goto(substr($_GET['q'], 11));
}

/**
 * Dummy access argument function
 */
function access_shib_login() {
  return TRUE;
}
/**
 * Generate the custom e-mail provider form
 * @returns HTML text of the custom e-mail form
 */
function shib_auth_custom_email() {
  $form = array();

  $form['custom_mail'] = array(
    '#type' => 'textfield',
    '#title' => t('E-mail'),
    '#size' => 60,
  );

  $form['submit'] = array(
    '#type' => 'submit',
    '#value' => t('Send'),
  );

  return $form;
} // function shib_auth_custom_email()
/**
 * E-mail validator
 * @param form form identifier
 * @param form_state $form_state contains all of the data of the form
 */
function shib_auth_custom_email_validate($form, &$form_state) {
  if ($form_state['values']['custom_mail'] == '') {
    form_set_error('', t('You have to fill the \'E-mail\' field.'));
  }
} // shib_auth_custom_email_validate()
//
/**
 * This function enables the administrator to clone an existing rule, this is useful,
 * when we want to create a rule, which is simiral to another one
 * @param id rule identifier
 */
function _shib_auth_clone_rule($id) {
  $rule = db_query("SELECT * FROM {shib_auth} WHERE id = %d", array($id));
  $db_entry = db_fetch_array($rule);
  $db_entry['id'] = NULL;
  $update = array();
  $ret = drupal_write_record('shib_auth', $db_entry, $update);
  if ($ret = SAVED_NEW) drupal_set_message('The rule has been successfulliy cloned.');
  else drupal_set_message('Unexpected error has been detected.');
  drupal_goto('admin/user/shib_auth/rules');
}//function _shib_auth_clone_rule()
/**
 * This function lets the admin to delete an existing rule
 * @param id rule identifier
 */
function _shib_auth_delete_rule($id) {
  db_query("DELETE FROM {shib_auth} WHERE id = %d", array($id));
  drupal_set_message('Rule <span style="font-weight: bold;">#'. $id .'</span> has been deleted.' , 'warning');
  drupal_goto('admin/user/shib_auth/rules');
}//function _shib_auth_delete_rule()
/**
 * This function lists all rules, and let the admin to do certain actions with them
 * @returns HTML table containing the attribute, RegExp, role and the actions, which can be done with each role
 */
function _shib_auth_list_rules() {
  $rules = db_query("SELECT * FROM {shib_auth}");
  $retval = '<table style="width: 100%;"><tr><th>Attribute</th><th>RegExp</th><th>Role(s)</th><th>Actions</th></tr>'."\n";
  $counter = 0;
  while ($rule = db_fetch_array($rules)) {
    $roles = unserialize(urldecode($rule['role']));
    $roles_list = '';
    if (!empty($roles)) $roles_list = implode(', ', $roles);
    $retval .= '<tr><td>'. $rule['field'] .'</td><td>'. urldecode($rule['regexpression']) .'</td><td>'. $roles_list .'</td>';
    $retval .= '<td stype="text-align: right;">';
    $retval .= '<a href="'. url('admin/user/shib_auth/clone/'. $rule['id']) .'">'. t('Clone') .'</a> | ';
    $retval .= '<a href="'. url('admin/user/shib_auth/edit/'. $rule['id']) .'">'. t('Edit') .'</a> | ';
    $retval .= '<a href="'. url('admin/user/shib_auth/delete/'. $rule['id']) .'">'. t('Delete') .'</a>';
    $retval .= '</td></tr>'."\n";
    $counter++;
  }
  if ($counter == 0) {
    $retval .= '<tr><td colspan="4" stype="text-align: center;">';
    $retval .= t('There is no rule in the database') .'</td></tr>'."\n";
  }
  $retval .= '</table>';

  return $retval;
} // function _shib_auth_list_rules()

/**
 * Alters user_login form for the shibboleth authentication module.
 *
 * @param $form The form.
 * @param $form_state contains all of the data of the form
 * @param $form_id The form ID.
 */
function shib_auth_form_alter(&$form, &$form_state, $form_id) {
  if ($form_id == 'user_login') {
    $form['shibboleth'] = array(
      '#type' => 'hidden',
      '#weight' => -1,
      '#prefix' => generate_login_text(),
      '#suffix' => '',
    );
  }
}
/**
 * Saves a new rule, containing he rule name, the server attrubite, the RegExp, and the role names
 *
 * @param $received_form - the identifier of the form, which we have just received
 * @returns an edit form, if there was a problem with the input values
 */
function shib_auth_new_rule($received_form) {
  $form = array();

  if ($received_form['post']['form_id'] == 'shib_auth_new_rule' ||
    $received_form['#parameters'][1]['post']['form_id'] == 'shib_auth_edit_rule') {

    $update = array();
    if (isset($received_form['#parameters'])) {
      $received_form = $received_form['#parameters'][1];
      $update = "id";
    }
    // if the received informations weren't empty
    if (!empty($received_form['post']['shib_auth_new_attrib']) &&
        !empty($received_form['post']['shib_auth_new_regexp'])) {

      $new_id = $received_form['post']['shib_auth_new_id'] == '0' ? NULL : (int) $received_form['post']['shib_auth_new_id'];
      // collect ther roles into an array
      $roles = array();
      if (is_array($received_form['post']['shib_auth_roles'])) {
        foreach ($received_form['post']['shib_auth_roles'] as $role_id) {
          $role_entry = db_query("SELECT * FROM {role} WHERE rid = %d", array($role_id));
          $role_ent = db_fetch_array($role_entry);
          $role = $role_ent['name'];
          $roles[$role_id] = $role;
        }
      }
      //save the new element into an array
      $new_element = array(
        'id'            => $new_id,
        'field'         => urlencode($received_form['post']['shib_auth_new_attrib']),
        'regexpression' => urlencode($received_form['post']['shib_auth_new_regexp']),
        'role'          => urlencode(serialize($roles)),
      );
      //write it in a record
      $ret = drupal_write_record('shib_auth', $new_element, $update);
      // if it wasn't an error
      if (empty($update)) {
        if ($ret = SAVED_NEW) drupal_set_message('New rule has been stored.');
        else drupal_set_message('Unexpected error has been detected.');
      }
      //an existing rule was updated
      else {
        if ($ret = SAVED_UPDATED) drupal_set_message('The rule has been modified.');
        else drupal_set_message('Unexpected error has been detected.');
      }
      //if everything was fine, print the rules with the newly added/modified one
      drupal_goto('admin/user/shib_auth/rules');
    }
  }
  // if something was wrang, print the edit form again
  return shib_auth_edit_form(array(0, '', '', '', 'Add rule'));
}//function shib_auth_new_rule()

/**
 * Edits an existing rule, containing he rule name, the server attrubite, the RegExp, and the role names
 *
 * @param $form_state contains all of the data of the form
 * @returns the edit form, with the fields already filled in
 */
function shib_auth_edit_rule($form_state, $id) {
  $form = array();
  // calls the edit form, with the fields of the existing rule
  if (is_int((int)$id)) {
    $rule = db_query("SELECT * FROM {shib_auth} WHERE id = %d", array($id));
    $db_entry = db_fetch_array($rule);
    return shib_auth_edit_form(
      array($db_entry['id'], $db_entry['field'], urldecode($db_entry['regexpression']), unserialize(urldecode($db_entry['role'])), 'Apply')
    );
  }

}//function shib_auth_edit_rule()
/**
 * Generate the shibboleth rule adding form
 *
 * @param $options contains the data, we want to fill the form with
 * @returns the edit form, with the fields already filled in with the elements of the options array
 */
function shib_auth_edit_form($options) {

  $form['shib_auth_new_id'] = array(
    '#title'          => t('Entry id'),
    '#type'           => 'hidden',
    '#default_value'  => $options[0],
  );

  $form['shib_auth_new_attrib'] = array(
    '#title'          => t('Shibboleth attribute name'),
    '#type'           => 'textfield',
    '#default_value'  => $options[1],
    '#require'        => TRUE,
    '#description'    => t('More properly: <b>$_SERVER</b> field name; enable DEBUG mode to list available fields. <br/>Note that it might differ from your users\' fields.'),
  );

  $form['shib_auth_new_regexp'] = array(
    '#title'          => t('Value (regexp)'),
    '#type'           => 'textfield',
    '#default_value'  => $options[2],
    '#require'        => TRUE,
  );

  $roles = user_roles(TRUE);

  $form['shib_auth_roles'] = array(
    '#type' => 'checkboxes',
    '#title' => t('Roles'),
    '#default_value' => count($options[3])>1||(count($options[3])==1 && $options[3] != "")?array_keys($options[3]):array(),
    '#options' => $roles,
  );

  $form['submit'] = array(
    '#type' => 'submit',
    '#value' => t($options[4]),
  );

  $form['#submit'][] = 'shib_auth_new_rule';

  return $form;
}//function shib_auth_edit_form()

/**
 * Admin users group membership validate
 *
 * @param $form data of the form
 * @param &$form_state contains all of the data of the form
 */
function shib_auth_admin_groups_validate($form, &$form_state) {

}//function shib_auth_admin_groups

/**
 * Admin users group membership submit
 *
 * @param $form data of the form
 * @param &$form_state contains all of the data of the form
 */
function shib_auth_admin_groups_submit($form, &$form_state) {
  variable_set('shib_auth_affilate_attrib', $form_state['values']['shib_auth_affilate_attrib']);
  drupal_set_message(t('Your changes are saved.'));
}//function shub_auth_groups_submit

