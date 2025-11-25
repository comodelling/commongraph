/*
 * SPDX-FileCopyrightText: 2019 JanusGraph Authors
 *
 * SPDX-License-Identifier: Apache-2.0
 */

// an init script that returns a Map allows explicit setting of global bindings.
def globals = [:]

// defines a sample LifeCycleHook that prints some output to the Gremlin Server console.
// note that the name of the key in the "global" map is unimportant.
globals << [hook : [
        onStartUp: { ctx ->
            ctx.logger.info("Executed once at startup of Gremlin Server.")
        },
        onShutDown: { ctx ->
            ctx.logger.info("Executed once at shutdown of Gremlin Server.")
        }
] as LifeCycleHook]

// define the default TraversalSource to bind queries to
globals << [g : graph.traversal()]
globals << [g_test : test.traversal()]
