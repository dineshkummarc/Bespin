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
import com.mozilla.bespin.mvc.Controller;
import com.mozilla.bespin.RequestContext;

/**
 * Dispatches the request to the appropriate controller
 */
public class Dispatcher
{
    private static final Map<HandlerMethod, DispatchMethod> dispatchMethods;

    static {
        Map<HandlerMethod, DispatchMethod> methods = new HashMap<HandlerMethod, DispatchMethod>();
        for (Class<? extends BespinController> dispatchClass : Arrays.asList(Edit.class, File.class, Register.class, Settings.class)) {
            for (Method m : dispatchClass.getMethods()) {
                if (m.getAnnotation(Dispatchable.class) != null) {
                    methods.put(new HandlerMethod(dispatchClass.getSimpleName(), m.getName()), new DispatchMethod(dispatchClass, m));
                }
            }
        }
        dispatchMethods = Collections.unmodifiableMap(methods);
    }

    private final Map<String, String> initParameters;
    private final ServletContext servletContext;

    public Dispatcher(ServletContext servletContext, Map<String, String> initParameters)
    {
        this.initParameters = initParameters;
        this.servletContext = servletContext;
    }

    public boolean dispatch(HttpServletRequest request, HttpServletResponse response) throws IOException
    {
        List<String> paths = new ArrayList<String>(Arrays.asList(request.getRequestURI().toLowerCase().substring(1).split("/")));
        String controllerName = StringUtils.capitalize(paths.remove(0));

        // if there's a path element, check for a method with that name
        DispatchMethod method = null;
        if (!paths.isEmpty()) {
            method = dispatchMethods.get(new HandlerMethod(controllerName, paths.get(0)));
            if (method != null) paths.remove(0); // if the method was found, remove that path element from the list b/c it is not an arg
        }

        // if the method is still null, check for a method with the name of the HTTP method
        if (method == null) method = dispatchMethods.get(new HandlerMethod(controllerName, request.getMethod().toLowerCase()));

        // if the method is still null, check for a default method
        if (method == null) method = dispatchMethods.get(new HandlerMethod(controllerName, "handler"));

        if (method != null) {
            Controller controller;
            try {
                controller = (Controller) method.getDispatchClass().newInstance();
            } catch (Exception e) {
                response.sendError(500, String.format("Controller \"%1$s\" could not be instantiated (%2$s)", controllerName, e.getClass() + ": " + e.getMessage()));
                return true;
            }
            RequestContext ctx = new RequestContext(servletContext, initParameters, request, response, paths);
            controller.setCtx(ctx);
            try {
                if (method.getDispatchMethod().isAnnotationPresent(RequiresLogin.class)) {
                    if (!controller.isAuthenticated()) {
                        response.sendError(401, "You're not logged in, and this request requires you to be");
                        return true;
                    }
                }

                // if there are any parameters, it'll be for a single RequestContext instance
                if (method.getDispatchMethod().getParameterTypes().length != 0) {
                    method.getDispatchMethod().invoke(controller, ctx);
                } else {
                    method.getDispatchMethod().invoke(controller);
                }
            } catch (Exception e) {
                e.printStackTrace();
                response.sendError(500, String.format("Error invoking method for request"));
            }
        } else {
            return false;
        }
        return true;
    }

    private static class HandlerMethod {
        private final String controller;
        private final String method;

        private HandlerMethod(String controller, String method) {
            this.controller = controller;
            this.method = method;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;

            HandlerMethod that = (HandlerMethod) o;

            if (!controller.equals(that.controller)) return false;
            if (!method.equals(that.method)) return false;

            return true;
        }

        @Override
        public int hashCode() {
            int result = controller.hashCode();
            result = 31 * result + method.hashCode();
            return result;
        }
    }

    private static class DispatchMethod {
        private final Class<?> dispatchClass;
        private final Method dispatchMethod;

        public DispatchMethod(Class<?> dispatchClass, Method dispatchMethod) {
            this.dispatchClass = dispatchClass;
            this.dispatchMethod = dispatchMethod;
        }

        public Class<?> getDispatchClass() {
            return dispatchClass;
        }

        public Method getDispatchMethod() {
            return dispatchMethod;
        }
    }
}