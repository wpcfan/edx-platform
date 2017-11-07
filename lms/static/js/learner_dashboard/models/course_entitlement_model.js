/**
 *  Store data to enroll learners into the course
 */
(function(define) {
    'use strict';

    define([
        'backbone'
    ],
        function(Backbone) {
            return Backbone.Model.extend({
                defaults: {
                    course_session_id: null,
                    available_sessions: []
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
