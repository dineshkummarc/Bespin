package com.mozilla.bespin;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import javax.servlet.ServletContext;
import java.util.*;

/**
 * Bag for state managed by {@link com.mozilla.bespin.mvc.FilterDispatcher}. Used in place of a {@link java.util.Map} to obviate need to cast for
 * common state types.
 */
public class RequestContext {
    private final HttpServletRequest req;
    private final HttpServletResponse resp;
    private final List<String> parameters = new ArrayList<String>();
    private final Map<String, String> initParameters;
    private final ServletContext servletContext;


    public RequestContext(ServletContext ctx, Map<String, String> initParameters, HttpServletRequest req, HttpServletResponse resp) {
        this(ctx, initParameters, req, resp, Collections.<String>emptyList());
    }

    public RequestContext(ServletContext ctx, Map<String, String> initParameters, HttpServletRequest req, HttpServletResponse resp, List<String> parameters) {
        this.servletContext = ctx;
        this.req = req;
        this.resp = resp;
        this.parameters.addAll(parameters);
        this.initParameters = initParameters;
    }

    public HttpServletRequest getReq() {
        return req;
    }

    public HttpServletResponse getResp() {
        return resp;
    }

    // -- Convenience
    public ServletContext getServletContext() {
        return servletContext;
    }

    public Map<String, String> getInitParameters() {
         return initParameters;
    }

    public HttpSession getSession() {
        return req.getSession();
    }

    /**
     * Guards against index out of bounds exceptions; returns null if the index is out of bounds
     *
     * @param index
     * @return
     */
    public String parameter(int index) {
        return (parameters.size() > index) ? parameters.get(index) : null;
    }

    /**
     * Returns an unmodifiable wrapper around the parameter list
     * 
     * @return
     */
    public List<String> getParameterList() {
        return Collections.unmodifiableList(parameters);
    }

    /**
     * Pops the first item off the parameter list
     *
     * @return
     */
    public String popParam() {
        return (parameters.isEmpty()) ? null : parameters.remove(0);
    }
}
