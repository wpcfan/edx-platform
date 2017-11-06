(function(define) {
    'use strict';

    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/learner_dashboard/models/course_enroll_model',
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
                     this.render();
                     this.entitlementModel = new EntitlementModel();
                 },

                 render: function() {
                    HtmlUtils.setHtml(this.$el, this.tpl({
                        cur_enrollment: "Hello World",
                    }));
                 },
             });
         }
    );
}).call(this, define || RequireJS.define);
