#!/usr/bin/python3
import numpy
import rospy

from optparse import OptionParser
from std_msgs.msg import String
from session import *

from pepper_nodes.srv import AnimationService, AnimationServiceResponse

class AnimationNode():
   '''
   A ROS (Robot Operating System) node designed for controlling animations in a robot. 
   This node communicates with the robot's Animation Service, enabling the execution of various animations 
   based on the received commands. It supports a range of animations like calm, explain, greet, happy, 
   showing tablet, and thinking, along with custom animations.

   Attributes:
   - _session (Session): A session object for communication with the robot.
   - _animation (ALAnimationPlayer): The animation player service used to run animations on the robot.

   Methods:
   - __init__(self, ip, port): Initializes the animation node, setting up a session and the animation service.
   - __call__(self): Starts the ROS node and establishes the animation service.
   - __animate(self, msg: AnimationService) -> AnimationServiceResponse: Handles the animation requests 
      based on the input message and executes the corresponding animation on the robot.
   '''
      
   def __init__(self, ip, port):
      '''
      Initializes the AnimationNode, creating a connection to the robot using the provided IP address and port.
      This method sets up the session and initializes the animation service for the robot.

      Args:
      - ip (str): The IP address of the robot.
      - port (int): The port number for establishing the connection.
      '''
      self._session = Session(ip, port)
      self._animation = self._session.get_service("ALAnimatedSpeech")

   def __call__(self):
      '''
      Starts the ROS node and establishes the Animation Service. This method creates and registers the service 
      to handle animation requests. It keeps the node running until an interruption occurs.
      '''
      rospy.init_node("animated_speech_node")
      rospy.Service('animated_speech_service', AnimationService, self.__animate)
      try:
         rospy.spin()
      except rospy.ROSInterruptException:
         pass

   # Private Methods
   def __animate(self, msg: AnimationService) -> AnimationServiceResponse:
        '''
        Handles animation requests by interpreting the input command and executing the corresponding animation.
        Supports predefined animations as well as custom animation strings. In case of an exception, it resets 
        the animation service and retries the animation execution.

        Args:
        - msg (AnimationService): The input message containing the animation command.

        Returns:
            AnimationServiceResponse: A response message indicating the completion of the animation request.
        '''
        try:
            animation_str = msg.input.data
            configuration = {"bodyLanguageMode":"contextual"}
            #rospy.loginfo(animation_str)
            self._animation.say(animation_str, configuration)
        except Exception as e:
            self._session.reconnect()
            self._animation = self._session.get_service("ALAnimatedSpeech")
            self._animation.say(animation_str, configuration)
            pass

if __name__ == "__main__":
   parser = OptionParser()
   parser.add_option("--ip", dest="ip", default="10.0.1.207")
   parser.add_option("--port", dest="port", default=9559)
   (options, args) = parser.parse_args()

   animation_node = AnimationNode(options.ip, int(options.port))
   animation_node()