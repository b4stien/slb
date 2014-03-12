class FamilyView

  constructor: (family) ->
    @family = family

  headerTpl: _.template("<tr>
    <th style='width:1px;'><%= view.family.name %></th>
    <% _.each(view.family.models, function(tool) { %> <th><%= tool.get('sn') %></th> <% }); %>
  </tr>")

  renderHeader: () ->
    @headerTpl view: @

  testTpl: _.template("<tr>
    <td><%= testID %></td>
    <% _.each(view.family.models, function(tool) { %> <%= view.renderCell(tool, testID) %> <% }); %>
  </tr>")

  renderTest: (testID) ->
    @testTpl testID: testID, view: @

  tpl: _.template("<table class='table table-bordered'>
    <%= view.renderHeader() %>
    <% _.each(view.family.tests, function(testID) { %> <%= view.renderTest(testID) %> <% }); %>
  </table>")

  renderCell: (tool, testID) ->
    "<td>#{tool.lastDate(testID).format('YYYY-MM-DD[T]HH:mm:ss[Z]')}</td>"

  render: () ->
    @tpl view: @
