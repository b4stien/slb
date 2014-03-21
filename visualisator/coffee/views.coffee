class FamilyView

  constructor: (el, family) ->
    @$ = el
    @family = family

    @family.tools.on 'change', () =>
      @render()

  headerTpl: _.template "<tr>
    <th></th>
    <% _.each(view.family.tools.models, function(tool) { %> <th><%= tool.get('sn') %></th> <% }); %>
  </tr>"

  renderHeader: () ->
    @headerTpl view: @

  testTpl: _.template "<tr>
    <th><%= test.name %></th>
    <% _.each(view.family.tools.models, function(tool) { %> <%= view.renderCell(tool, test.id) %> <% }); %>
  </tr>"

  renderTest: (test) ->
    @testTpl test: test, view: @

  cellTpl: _.template "<td class='test <%= toolTest.status() %>'>
    <% if(toolTest.lastMat()) { %>
      <span class='test-status'><%= toolTest.lastMat().status %></span><% if(toolTest.lastMat().tfl) { %> - <a href='<%= toolTest.lastMat().tfl %>'>TFL</a><% } %>
      <span class='test-timestamp'><%= toolTest.lastDate().format(window.momentFormat) %></span>
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
    <% _.each(view.family.get('tests'), function(test) { %> <%= view.renderTest(test) %> <% }); %>
  </table>")

  render: () ->
    @$.html @tpl view: @
