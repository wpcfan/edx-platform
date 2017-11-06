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
                    is_fulfilled: false,
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
