package com.mozilla.bespin.mvc;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

/**
 * Marks a method as being dispatchable from a HTTP request
 */
@Retention(RetentionPolicy.RUNTIME)
public @interface Dispatchable {
}
