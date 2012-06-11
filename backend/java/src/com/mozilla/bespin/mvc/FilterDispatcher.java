package com.mozilla.bespin.mvc;

import org.apache.commons.lang.StringUtils;

import javax.servlet.*;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.lang.reflect.Method;
import java.util.*;

import com.mozilla.bespin.controllers.*;
import com.mozilla.bespin.mvc.Dispatchable;
import com.mozilla.bespin.mvc.RequiresLogin;
import com.mozilla.bespin.mvc.Dispatcher;

/**
 * Invokes the dispatcher from a Servlet filter
 */
public class FilterDispatcher implements Filter {
    private Dispatcher dispatcher;

    public void init(FilterConfig filterConfig) throws ServletException {
        Map<String, String> params = new HashMap<String, String>();
        for (Enumeration e = filterConfig.getInitParameterNames(); e.hasMoreElements();) {
            String key = e.nextElement().toString();
            params.put(key, filterConfig.getInitParameter(key));
        }
        this.dispatcher = new Dispatcher(filterConfig.getServletContext(), Collections.unmodifiableMap(params));
    }

    public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain filterChain) throws IOException, ServletException {
        if (!dispatcher.dispatch((HttpServletRequest) servletRequest, (HttpServletResponse) servletResponse)) {
            filterChain.doFilter(servletRequest, servletResponse);
        }
    }

    public void destroy() {
    }
}
