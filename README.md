# Telegram bot for speed-dating
The main goal of the bot is to provide speed-dating system, based on Jitsi. <br />
For each user another anonymous user with the best priority(about priorities read below) is selected and then they'll go on online date using Jitsi.

# Priorities
Priorities are a set of some factors that determine the weight of the candidate for current user:
  * University speciality
  * University course
  * University group

**Here's a table of priorities(from high to low)**:
  * *Same course, same speciality, same group*
  * *Same course, different specialities*
  * *Same course, same speciality, same group*
  * *Different courses, same speciality*
  * *Different courses, different speciality*
  * *None of them*
  
# Commands
**User commands**:
  * /register - registration
  * /edit - change information about yourself
  * /whoami - shows information about yourself
  * **/find_partner** - find partner for date, if partner is not finded - user goes to queue

**Admin commands**:
  * /show_hierarchy - indication of tree type: Specialty - Group(used in process of registration to choose your speciality and it's group)
  * /add_node - adds a node to the tree. If number of arguments is 1 - a specialty will be created, if 2 - group of some speciality will be created
  (e.g: /add_node TestGroup, TestSpeciality -> in this example group named TestGroup was created for speciality named TestSpeciality)
  * /edit_node - same as above, only changes the name
  * /delete_node - delete node of the tree. If speciality was deleted - all child groups will be also deleted
  * /delete_hierarchy - deletes the entire tree
  
**Super-admin commands**: <br />

Super-admins have same commands as the regular admins, but also have: 
  * /add_admin - adds an admin
  * /promote_admin - promotes admin to superuser
  * /demote_admin - demotes to regular admin

