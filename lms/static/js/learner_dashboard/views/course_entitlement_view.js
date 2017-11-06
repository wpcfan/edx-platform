(function(define) {
    'use strict';

    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/learner_dashboard/models/course_entitlement_model',
        'text!../../../templates/learner_dashboard/course_entitlement.underscore'
    ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             EntitlementModel,
             pageTpl
         ) {
             return Backbone.View.extend({
                 tpl: HtmlUtils.template(pageTpl),

                 initialize: function(options) {
                     this.$el = options.$el;
                     this.entitlementModel = new EntitlementModel();
                     this.render(options);
                 },

                 render: function(options) {
                    var data = $.extend(this.entitlementModel.toJSON(), {
                        course_session_id: options.$data['course_session_id'],
                        available_sessions: options.$data['available_sessions'],
                    });
                    HtmlUtils.setHtml(this.$el, this.tpl(data));
                 },
             });
         }
    );
}).call(this, define || RequireJS.define);
