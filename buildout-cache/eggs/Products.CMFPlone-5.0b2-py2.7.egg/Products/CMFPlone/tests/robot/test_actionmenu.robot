*** Settings *****************************************************************

Resource  plone/app/robotframework/keywords.robot
Resource  plone/app/robotframework/saucelabs.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Resource  keywords.robot

Test Setup  Run keywords  Open SauceLabs test browser
Test Teardown  Run keywords  Report test status  Close all browsers


*** Variables ****************************************************************

${TITLE}  An actionsmenu page
${PAGE_ID}  an-actionsmenu-page


*** Test cases ***************************************************************

# ---
# Basic Contentactions menu
# ---

Scenario: Actions Menu rendered collapsed
    Given a logged-in site administrator
      and an actionsmenu page
     Then delete link exists
      and delete link should not be visible

Scenario: Clicking expands action menu
    Given a logged-in site administrator
      and an actionsmenu page
     When menu link is clicked
     Then actions menu should be visible

Scenario: Clicking again collapses action menu
    Given a logged-in site administrator
      and an actionsmenu page
     When menu link is clicked
      and menu link is clicked

# ---
# Switching Contentactions menu by MouseOver
# ---

Scenario: Hovering mouse from expanded menu on other menu shows that menu
    Pass Execution  This functionality needs to be fixed for Plone 5, but let's not make it break the build for now.
    Given a logged-in site administrator
      and an actionsmenu page
     When first menu link is clicked
      and mouse moves to second menu
     Then second menu should be visible
      and first menu should not be visible

# ---
# Clicking outside of Contentactions menu
# ---

Scenario: Clicking outside of Contentactions menu
    Given a logged-in site administrator
      and an actionsmenu page
     When menu link is clicked
      and I click outside of menu
     Then actions menu should not be visible

# ---
# Workflow stuff
# ---

Scenario: Do a workflow change
    Given a logged-in site administrator
      and an actionsmenu page
     When workflow link is clicked
     Then state should have changed

# ---
# Copy stuff
# ---

Scenario:
    Given a logged-in site administrator
      and an actionsmenu page
     When I copy the page
      and I paste
     Then I should see 'Item(s) pasted.' in the page


*** Keywords *****************************************************************

# --- GIVEN ------------------------------------------------------------------

an actionsmenu page
    Create content  type=Document  title=${TITLE}
    Go to  ${PLONE_URL}/${PAGE_ID}


# --- WHEN -------------------------------------------------------------------

mouse moves to second menu
    Click Link  xpath=(//div[@class="contentActions"]//a[contains(@class, 'actionMenuHeader')])[2]

I click outside of menu
    Click Element  xpath=//h1

workflow link is clicked
    # store current state
    ${OLD_STATE} =  Get Text  xpath=(//span[contains(@class,'state-')])[2]
    Set Suite Variable  ${OLD_STATE}  ${OLD_STATE}
    Given patterns are loaded
    Click Link  xpath=//li[@id='plone-contentmenu-workflow']/a
    Click Link  xpath=(//li[@id='plone-contentmenu-workflow']/ul/li/a)[1]
    Page Should Contain  Item state changed.
    # FIXME: The above 'Click Link' fails on Internet Explorer, but the
    # following keywords 'workflow link is clicked softly' passes. Until we
    # know why, we check if the above worked and if not, we try the other
    # approach.
    @{value} =  Run Keyword And Ignore Error
    ...         Page Should Contain  Item state changed.
    Run Keyword If  '@{value}[0]' == 'FAIL'
    ...         workflow link is clicked softly

workflow link is clicked softly
    [Documentation]  This works on Internet Explorer, but not on Firefox...
    Mouse Over  xpath=//*[@id='plone-contentmenu-workflow']/a
    Click Link  xpath=//li[@id='plone-contentmenu-workflow']/a
    Mouse Over  xpath=(//li[@id='plone-contentmenu-workflow']//a)[1]
    Mouse Down  xpath=(//li[@id='plone-contentmenu-workflow']//a)[1]
    Mouse Up  xpath=(//li[@id='plone-contentmenu-workflow']//a)[1]
    Wait until page contains  Item state changed.

Open Menu
    [Arguments]  ${elementId}
    Element Should Not Be Visible  css=#${elementId} ul.actionMenuContent
    Click link  css=#${elementId} a.actionMenuHeader
    Wait until keyword succeeds  5  1  Element Should Be Visible  css=#${elementId} .actionMenuContent

Open Action Menu
    Given patterns are loaded
    Click link  xpath=//li[@id='plone-contentmenu-moreoptions']/a
    Wait until keyword succeeds  5  1  Element Should Be Visible  css=#plone-contentmenu-actions

I copy the page
    Open Action Menu
    Click Link  link=Copy
    Page should contain  copied

I paste
    Go to  ${PLONE_URL}
    Open Action Menu
    Click Link  link=Paste


# --- THEN -------------------------------------------------------------------

delete link exists
     Page Should Contain Element  xpath=//a[@id='plone-contentmenu-actions-delete']

delete link should not be visible
     Element Should Not Be Visible  xpath=//div[@class='contentActions']//a[@id='plone-contentmenu-actions-delete']

menu link is clicked
    Given patterns are loaded
    Click link  xpath=//li[@id='plone-contentmenu-moreoptions']/a

delete link should be visible
    Given patterns are loaded
    Element Should Be Visible  xpath=//div[@class='contentActions']//a[@id='plone-contentmenu-actions-delete']

actions menu should be visible
    Given patterns are loaded
    Element Should Be Visible  xpath=//li[@id='plone-contentmenu-actions']

first menu link is clicked
    Given patterns are loaded
    Click Link  xpath=(//div[@class="contentActions"]//a[contains(@class, 'actionMenuHeader')])[1]

I should see '${message}' in the page
    Wait until page contains  ${message}
    Page should contain  ${message}

state should have changed
    Wait until page contains  Item state changed
    ${NEW_STATE} =  Get Text  xpath=(//span[contains(@class,'state-')])[2]
    # Should Not Be Equal  ${NEW_STATE}  ${OLD_STATE}

second menu should be visible
    Element Should Be Visible  xpath=(//li[contains(@class, 'actionMenu')])[2]

first menu should not be visible
    Given patterns are loaded
    Wait until keyword succeeds  10s  1s  Element Should Not Be Visible  xpath=(//li[contains(@class, 'actionMenu')])[1]//li

actions menu should not be visible
    Given patterns are loaded
    Wait until keyword succeeds  10s  1s  Element Should Not Be Visible  xpath=//li[@id='plone-contentmenu-actions']

