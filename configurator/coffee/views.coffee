class FamilyView

  constructor: (el, family) ->
    @family = family
    @el = el
    @$ = @el

    @family.on 'change:configType', () =>
      @render()

  tpl: _.template "<div class='well well-sm'>
      <button type='button' class='close'>×</button>

      <div class='form-group'>
        <label><b>Family name</b></label>
        <input class='form-control family-name' type='text' placeholder='Family name' value='<%= family.get('name') %>'>
      </div>

      <div class='row'>
        <div class='col-xs-4 family-config-type-specific'>
        </div>

        <div class='col-xs-8'>
          <h5><b>Tests (ordered)</b><a href='#' class='add-test' style='color:#333; float:right; margin-right:12px;'><i class='fa fa-plus-circle'></i></a></h5>
          <div class='tests'></div>
        </div>
      </div>
    </div>"

  serialNumbersTpl : _.template "<h5><b>Tools</b><a href='#' class='add-sn' style='color:#333; float:right; margin-right:12px;'><i class='fa fa-plus-circle'></i></a></h5>
  <div class='serial-numbers'></div>"

  dateTpl : _.template "<h5><b>Serial numbers prefix</b></h5>
    <input class='form-control family-serial-numbers-prefix' type='text' placeholder='' value='<%= family.get('serialNumbersPrefix') %>'>"

  toolTpl: _.template "<div class='form-group'><div class='input-group'>
      <input type='text' class='form-control' placeholder='Serial number' value='<%= serialNumber %>'>
      <span class='input-group-btn'>
        <button class='remove btn btn-default' type='button'><i class='fa fa-trash-o'></i></button>
      </span>
    </div></div>"

  testTpl: _.template "<div class='test form-inline' style='margin-bottom:15px;'>
      <div class='form-group'>
        <input style='width:257px;' type='text' class='test-name form-control' placeholder='Test name' value='<%= name %>'>
      </div>
      <div class='form-group'>
        <input type='text' class='test-id form-control' placeholder='Test ID' value='<%= id %>'>
      </div>
      <button class='remove btn btn-default' type='button'><i class='fa fa-trash-o'></i></button>
    </div>"

  buildTest: (test) ->
    jQtest = $ @testTpl test

    jQtest.on 'click', '.remove', () =>
      jQtest.remove()
      @$.find('.tests').trigger 'change'

  buildTool: (tool) ->
    jQtool = $ @toolTpl tool

    jQtool.on 'click', '.remove', () =>
      jQtool.remove()
      @$.find('.serial-numbers').trigger 'change'

  render: () ->
    @$.html @tpl family: @family

    if @family.get('configType') == 'serialNumbers'
      specificTpl = @serialNumbersTpl

    else if @family.get('configType') == 'date'
      specificTpl = @dateTpl

    @$.find('.family-config-type-specific').html specificTpl family: @family

    for serialNumber in @family.get 'tools'
      jQtool = @buildTool serialNumber: serialNumber
      @$.find('.serial-numbers').append jQtool

    for test in @family.get 'tests'
      jQtests = @buildTest test
      @$.find('.tests').append jQtests

    @$.find('.close').on 'click', (e) =>
      window.families = _.without window.families, @family
      window.generateConfig()
      @el.remove()

    @$.find('.family-name').on 'change keyup', (e) =>
      @family.set 'name', $(e.currentTarget).val()

    @$.find('.tests').on 'change keyup', () =>
      tests = []
      @$.find('.tests').find('.test').each (idx, el) ->
        test = {}
        test['name'] = $(el).find('.test-name').val()
        test['id'] = $(el).find('.test-id').val()
        tests.push test
      @family.set 'tests', tests

    @$.find('.serial-numbers').on 'change keyup', () =>
      sns = []
      @$.find('.serial-numbers').find('input').each (idx, el) ->
        sns.push $(el).val()
      @family.set 'tools', sns

    @$.find('.family-serial-numbers-prefix').on 'change keyup', (e) =>
      @family.set 'serialNumbersPrefix', $(e.currentTarget).val()

    @$.find('.add-test').on 'click', (e) =>
      test = @buildTest name: '', id: ''

      @$.find('.tests').append test
      @$.find('.tests').trigger 'change'
      e.preventDefault()


    @$.find('.add-sn').on 'click', (e) =>
      sn = @buildTool serialNumber: ''

      @$.find('.serial-numbers').append sn
      @$.find('.serial-numbers').trigger 'change'
      e.preventDefault()
