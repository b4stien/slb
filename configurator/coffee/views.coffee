class FamilyView

  constructor: (el, family) ->
    @family = family
    @el = el
    @$ = @el

  tpl: _.template "<div class='well well-sm'>
      <button type='button' class='close'>×</button>

      <div class='row'>
        <div class='col-xs-6'>
          <div class='form-group'>
            <label><b>Family name</b></label>
            <input class='form-control family-name' type='text' value=''>
          </div>
        </div>
      </div>

      <div class='row'>
        <div class='col-xs-6'>
          <h5><b>Serial numbers</b><a href='#' class='add-sn' style='color:#333; float:right; margin-right:12px;'><i class='fa fa-plus-circle'></i></a></h5>
          <div class='serial-numbers'></div>
        </div>

        <div class='col-xs-6'>
          <h5><b>Test IDs (ordered)</b><a href='#' class='add-test' style='color:#333; float:right; margin-right:12px;'><i class='fa fa-plus-circle'></i></a></h5>
          <div class='tests'></div>
        </div>
      </div>
    </div>"

  fieldTpl: _.template "<div class='form-group'><div class='input-group'>
      <input type='text' class='form-control'>
      <span class='input-group-btn'>
        <button class='remove btn btn-default' type='button'><i class='fa fa-trash-o'></i></button>
      </span>
    </div></div>"

  render: () ->
    @$.html @tpl()

    @$.find('.close').on 'click', (e) =>
      window.families = _.without window.families, @family
      window.stampConfig()
      @el.remove()

    @$.find('.family-name').on 'change keyup', (e) =>
      @family.set 'name', $(e.currentTarget).val()

    @$.find('.tests').on 'change keyup', () =>
      tests = []
      @$.find('.tests').find('input').each (idx, el) ->
        tests.push $(el).val()
      @family.set 'tests', tests

    @$.find('.serial-numbers').on 'change keyup', () =>
      sns = []
      @$.find('.serial-numbers').find('input').each (idx, el) ->
        sns.push $(el).val()
      @family.set 'tools', sns

    @$.find('.add-test').on 'click', (e) =>
      test = $ @fieldTpl()

      test.on 'click', '.remove', () =>
        test.remove()
        @$.find('.tests').trigger 'change'

      @$.find('.tests').append test
      @$.find('.tests').trigger 'change'
      e.preventDefault()


    @$.find('.add-sn').on 'click', (e) =>
      sn = $ @fieldTpl()

      sn.on 'click', '.remove', () =>
        sn.remove()
        @$.find('.serial-numbers').trigger 'change'

      @$.find('.serial-numbers').append sn
      @$.find('.serial-numbers').trigger 'change'
      e.preventDefault()
