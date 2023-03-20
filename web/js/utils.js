/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import naturalCompare from "natural-compare-lite";

export const promiseFinally = (promise, final) =>
  promise.then(
    (response) => Promise.resolve(final()).then(() => response),
    (err) => Promise.resolve(final()).then(() => Promise.reject(err)),
  );

export const isJsObject = (obj) =>
  _.isObject(obj) && !_.isFunction(obj) && !_.isArray(obj);

export const isUndefinedOrNull = (arg) => arg === undefined || arg === null;

export const isDefinedAndNotNull = (arg) => !isUndefinedOrNull(arg);

export const startsWith = (baseString, searchString) =>
  baseString.indexOf(searchString) === 0;

// Returns the first non-undefined and non-null argument.
// Returns undefined if there are no such arguments.
export const coalesce = (...args) =>
  _.find(args, (a) => isDefinedAndNotNull(a));

export const maybeAsNumber = (text) =>
  _.isFinite(text) ? parseFloat(text) : text;

export const isPositiveInteger = (arg) => arg === parseInt(arg, 10) && arg >= 0;

export function ignoreBlanks(text) {
  if (text === "") {
    return null;
  }
  return text;
}

export function deepCopyJson(obj) {
  if (isUndefinedOrNull(obj)) {
    return obj;
  }
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Use `withPreventDefault` to create callback functions that accept an `event` argument
 * and call event.preventDefault() on it. This is useful when you want to add an eventHandler
 * and don't want to concern yourself with the event argument. For example, if you were to
 * say <a href="/plans" onClick={myEventHandler}>Link</a>, then the "default" action is to
 * navigate to /plans, which will happen after your `myEventHandler` executes. The standard
 * way to handle this is to call event.withPreventDefault(). Or, you can use this method
 * and just write <a href="/plans" onClick={withPreventDefault(myEventHandler)}>Link</a>.
 *
 * withStopPropagation and withPreventDefaultAndStopPropagation are similar.
 */
export const withPreventDefault = (f) =>
  function (...args) {
    const event = args[0];
    if (event) {
      event.preventDefault();
    }
    f.apply(this, args);
  };

export const withStopPropagation = (f) =>
  function (...args) {
    const event = args[0];
    if (event) {
      event.stopPropagation();
    }
    f.apply(this, args);
  };

export const withPreventDefaultAndStopPropagation = (f) =>
  function (...args) {
    const event = args[0];
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    f.apply(this, args);
  };

function isNothing(obj) {
  if (_.isArray(obj) || isJsObject(obj)) {
    return _.isEmpty(obj);
  }
  return isUndefinedOrNull(obj);
}

export const isNotNothing = (obj) => !isNothing(obj);

export function renderNumber(num, round) {
  const roundNumber = (n) => {
    if (!round) {
      return n.toString();
    }
    const rounded = n.toPrecision(6);
    if (Number(rounded) === n) {
      return n.toString();
    }
    return rounded;
  };
  if (_.isNumber(num)) {
    return roundNumber(num);
  } else if (_.isFinite(num)) {
    return roundNumber(parseFloat(num));
  }
  return num;
}

export function recursivelyCondenseObject(obj) {
  if (_.isArray(obj)) {
    return _.chain(obj)
      .map((v) => recursivelyCondenseObject(v))
      .filter(isNotNothing)
      .value();
  } else if (isJsObject(obj)) {
    return _.chain(obj)
      .mapObject((o) => recursivelyCondenseObject(o))
      .pick(isNotNothing)
      .value();
  }
  return obj;
}

export function recursivelyOmitKeys(obj, keys) {
  if (_.isArray(obj)) {
    return _.map(obj, (value) => recursivelyOmitKeys(value, keys));
  } else if (isJsObject(obj)) {
    const objCopy = _.omit(obj, keys);
    _.each(objCopy, (value, key) => {
      objCopy[key] = recursivelyOmitKeys(value, keys);
    });
    return objCopy;
  } else {
    return obj;
  }
}

export const editKey = () => `edit_key_${Math.random()}`;

export const idKey = ({id}) => parseInt(id, 10);

export function naturalStringCompare(a, b) {
  const undefinedArgs = _.map(isUndefinedOrNull, [a, b]);
  if (_.any(undefinedArgs)) {
    const [undefA, undefB] = undefinedArgs;
    return Number(undefB) - Number(undefA);
  }
  return (
    naturalCompare(a.toLowerCase(), b.toLowerCase()) || naturalCompare(a, b)
  );
}

export function colorHexToRGB(hex) {
  const raise = () => {
    throw new Error(`Invalid color hex: ${hex}`);
  };
  if (isUndefinedOrNull(hex)) {
    raise();
  }
  if (!hex.match(/^#[a-fA-F0-9]{6}$/u)) {
    raise();
  }
  const int32Value = parseInt(hex.substr(1), 16);
  /* eslint-disable no-bitwise */
  return {
    r: (0xff0000 & int32Value) >> 16,
    g: (0x00ff00 & int32Value) >> 8,
    b: 0x0000ff & int32Value,
  };
  /* eslint-enable no-bitwise */
}

const toSet = (data, iteratee) =>
  _.chain(data)
    .map(_.iteratee(iteratee))
    .map((item) => [item, true])
    .object()
    .value();

export const areSetsEqual = (lhs, rhs, iteree) =>
  _.isEqual(toSet(lhs, iteree), toSet(rhs, iteree));

// NOTE: once there's enough browser support for String.prototype.replaceAll, switch to more natural
// text.replaceAll(search, replaceWith)
export const replaceAll = (text, search, replaceWith) =>
  text.split(search).join(replaceWith);

export function eachWithDelay(data, iteratee, delay_) {
  // delay should be a number of seconds or a function that returns a number of seconds (ie. a random number generator)
  let delay;
  if (_.isFunction(delay_)) {
    delay = delay_;
  } else {
    delay = () => delay_;
  }
  const items = _.pairs(data).reverse();
  return new Promise((success, error) => {
    const nextIteration = (timeout) => {
      if (_.isEmpty(items)) {
        return success(data);
      }
      return setTimeout(loopWithDelay, timeout);
    };
    function loopWithDelay() {
      try {
        iteratee(...items.pop().reverse());
      } catch (e) {
        return error(e);
      }
      return nextIteration(1000 * delay());
    }
    // defer the first call so that the stack behavior is identical regardless of the size of the input
    _.defer(nextIteration, 0);
  });
}

export function uniformRandomNumberGenerator(min, max) {
  return () => Math.random() * (max - min) + min;
}
