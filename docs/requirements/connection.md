## Connection Page

The connection page is the default starting page of SonicControl, so that the user can connect to a SonicDevice system. The user connects to the SonicDevice by choosing the port adress and pressing the connect button. After a connection was established, the firmware information of the SonicDevice is shown and the possibilty to disconnect is presented.

### Requirements

- After the connection attempt, the page shows the ongoing process (progressbar or animating three dots)
- If the connection attempt fails, the user is shown a message and a log report
  - If a connection is possible, but the device itself is unkown, the user can activate the Serial Monitor to try and speak to the device
- After a successfull connection was established, the firmware information about the SonicDevice is shown
- During an established connection, the user can disconnect. By the action of disconnection SonicControl goes into "Not connected"- mode
