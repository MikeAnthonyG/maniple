
'use strict';

const app = require('../../src/app.js');
const chai = require('chai')
const expect = chai.expect;
var event, context;

describe('Tests return hello world', function() {
    it('verifies successful response', () => {
        const result = app.handler(event, context);
        expect(result).to.be.equal('hello world');
    });
})
