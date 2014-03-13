class FamilyView

  constructor: (family) ->
    @family = family

  headerTpl: _.template "<tr>
    <th></th>
    <% _.each(view.family.tools.models, function(tool) { %> <th><%= tool.get('sn') %></th> <% }); %>
  </tr>"

  renderHeader: () ->
    @headerTpl view: @

  testTpl: _.template "<tr>
    <td><%= testID %></td>
    <% _.each(view.family.tools.models, function(tool) { %> <%= view.renderCell(tool, testID) %> <% }); %>
  </tr>"

  renderTest: (testID) ->
    @testTpl testID: testID, view: @

  cellTpl: _.template "<td class='test <%= toolTest.status() %>'>
    <% if(toolTest.lastMat()) { %>
      <span class='test-status'><%= toolTest.lastMat().status %></span><% if(toolTest.lastMat().tfl) { %> - <a href='<%= toolTest.lastMat().tfl %>'>TFL</a><% } %>
      <span class='test-timestamp'><%= toolTest.lastDate().format('YYYY-MM-DD[T]HH:mm:ss[Z]') %></span>
    <% } else { %>
      <span class='test-status'>None</span>
    <% } %>
  </td>"

  renderCell: (tool, testID) ->
    toolTest = tool.getToolTest(testID)
    @cellTpl toolTest: toolTest

  tpl: _.template("<h3><%= view.family.get('name') %></h2>
  <table class='family table table-bordered'>
    <%= view.renderHeader() %>
    <% _.each(view.family.get('tests'), function(testID) { %> <%= view.renderTest(testID) %> <% }); %>
  </table>")

  render: () ->
    @tpl view: @
