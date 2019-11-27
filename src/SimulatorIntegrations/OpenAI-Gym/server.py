import grpc
from concurrent import futures
import numpy as np
import time

import gym

from OpenAIEnv import Envs

import services.simulator_pb2 as simulator_pb2
import services.simulator_pb2_grpc as simulator_pb2_grpc

import logging
logger = logging.getLogger('werkzeug')
logger.setLevel(logging.ERROR)

# Our environments being used
envs = Envs()

class SimulatorServicer(simulator_pb2_grpc.SimulatorServicer):
    def Create(self, request, context):
        logger.info("Creating environment %s" % (request.envId))
        response = simulator_pb2.SimulatorCreateResponse()
        response.instanceId = envs.create(request.envId)
        return response

    # def step(self, instance_id, action, render):
    def Step(self, request, context):
        logger.info("Stepping through instance %s" % (request.instanceId))
        response = simulator_pb2.SimulatorStepResponse()

        # Returns obs_jsonable, reward, done, info
        result = envs.step(request.instanceId, request.action, request.render)
        
        response.reward = result[1]
        response.isDone = result[2]
        # response.info = result[3]

        # Get the ObservationSpace metadata
        osi = envs.get_observation_space_info(request.instanceId)

        if osi['name'] == 'Discrete':
            response.observationDiscrete.observation = result[0]
        elif osi['name'] == 'Box':
            response.observationBox.dimensions.extend(np.asarray(osi['shape'])) 
            response.observationBox.observation.extend(result[0])
        else:
            logger.error("Unsupported Space Type: %s" % info['name'])
            logger.error(info)

        
        logger.info("Step returned %s" % (response))

        return response

    def Reset(self, request, context):
        logger.info("Resetting instance %s" % (request.instanceId))
        response = simulator_pb2.SimulatorResetResponse()

        envObservation = envs.reset(request.instanceId)
        response.observation.extend(envObservation)

        return response

    def Close(self, request, context):
        logger.info("Closing instance %s" % (request.instanceId))
        envs.env_close(request.instanceId)
        return simulator_pb2.SimulatorCloseResponse() # Empty response

    def Render(self, request, context):
        logger.info("Closing instance %s" % (request.instanceId))
        envs.render(request.instanceId)
        return simulator_pb2.SimulatorCloseResponse() # Empty response

    def MonitorStart(self, request, context):
        logger.info("Monitor Start for instance %s" % (request.instanceId))
        envs.monitor_start(request.instanceId, './monitor', True, False, 10)
        return simulator_pb2.BaseResponse() # Empty response

    def MonitorStop(self, request, context):
        logger.info("Monitor Stop for instance %s" % (request.instanceId))
        envs.monitor_close(request.instanceId)
        return simulator_pb2.BaseResponse() # Empty response

    def ActionSpaceSample(self, request, context):
        response = simulator_pb2.SimulatorActionSpaceSampleResponse()
        action = envs.get_action_space_sample(request.instanceId)
        response.action = action
        logger.info("Sampled Action Space %s" % (response))
        return response
        
    def ActionSpaceInfo(self, request, context):
        response = simulator_pb2.SimulatorActionSpaceInfoResponse()

        info = envs.get_action_space_info(request.instanceId)
        response.name = info['name']

        if info['name'] == 'Discrete':
            # response.typeDiscrete = simulator_pb2.ObservationSpaceTypeDiscrete()
            response.typeDiscrete.n = info['n']
        elif info['name'] == 'Box':
            # response.typeBox = simulator_pb2.ObservationSpaceTypeBox()
            response.typeBox.shape.extend(np.asarray(info['shape'])) # Convert the shape tuple to an array
            response.typeBox.low.extend(info['low'])
            response.typeBox.high.extend(info['high'])
        else:
            logger.error("Unsupported Space Type: %s" % info['name'])
            logger.error(info)

        return response
        
    def ObservationSpaceInfo(self, request, context):
        response = simulator_pb2.SimulatorObservationSpaceInfoResponse()

        info = envs.get_observation_space_info(request.instanceId)
        response.name = info['name']

        if info['name'] == 'Discrete':
            # response.typeDiscrete = simulator_pb2.ObservationSpaceTypeDiscrete()
            response.typeDiscrete.n = info['n']
        elif info['name'] == 'Box':
            # response.typeBox = simulator_pb2.ObservationSpaceTypeBox()
            response.typeBox.shape.extend(np.asarray(info['shape'])) # Convert the shape tuple to an array
            response.typeBox.low.extend(info['low'])
            response.typeBox.high.extend(info['high'])
        else:
            logger.error("Unsupported Space Type: %s" % info['name'])
            logger.error(info)

        return response
        

# Create the gRPC server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

# use the generated function `add_SimulatorServicer_to_server` to add the defined class to the server
simulator_pb2_grpc.add_SimulatorServicer_to_server(SimulatorServicer(), server)

# listen on port 50051
print('Starting server. Listening on port 50051.')
server.add_insecure_port('[::]:50051')
server.start()

# since server.start() will not block,
# a sleep-loop is added to keep alive
try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    server.stop(0)