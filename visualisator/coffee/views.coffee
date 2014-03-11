class FamilyView

  constructor: (family) ->
    @family = family

  headerTpl: _.template("<tr>
    <th style='width:1px;'><%= view.family.get('name') %></th>
    <% _.each(view.family.tools.models, function(tool) { %> <th><%= tool.get('sn') %></th> <% }); %>
  </tr>")

  renderHeader: () ->
    @headerTpl view: @

  testTpl: _.template("<tr>
    <td><%= testID %></td>
    <% _.each(view.family.tools.models, function(tool) { %> <%= view.renderCell(tool, testID) %> <% }); %>
  </tr>")

  renderTest: (testID) ->
    @testTpl testID: testID, view: @

  renderCell: (tool, testID) ->
    lastDate = tool.lastDate(testID)
    if lastDate
      return "<td>#{tool.lastDate(testID).format('YYYY-MM-DD[T]HH:mm:ss[Z]')}</td>"
    "<td>None</td>"

  tpl: _.template("<table class='table table-bordered'>
    <%= view.renderHeader() %>
    <% _.each(view.family.get('tests'), function(testID) { %> <%= view.renderTest(testID) %> <% }); %>
  </table>")

  render: () ->
    @tpl view: @
