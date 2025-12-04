import sys
from PyQt5.QtWidgets import QColorDialog,QFileDialog, QApplication, QMainWindow, QFrame, QToolBar, QPushButton, QVBoxLayout, QMenu, QWidget, QLabel, QHBoxLayout, QSlider, QAction, QMessageBox
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
from PyQt5 import QtCore

from vtkmodules.all import *

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton
import math
import vtk
from vtkmodules.vtkCommonDataModel import (
    vtkConvexPointSet,
    vtkPolyData,
    vtkUnstructuredGrid,
    vtkQuadric
)
import vtk
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkImagingHybrid import vtkSampleFunction
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkGlyph3DMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersSources import vtkSphereSource, vtkParametricFunctionSource
from vtkmodules.vtkCommonComputationalGeometry import (
    vtkParametricKlein, vtkParametricTorus, vtkParametricMobius,
    vtkParametricEllipsoid, vtkParametricSuperEllipsoid) 

import vtk
import math
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from collections import namedtuple
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonCore import vtkLookupTable
from vtkmodules.vtkFiltersSources import vtkPlatonicSolidSource
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkActor2D,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer,
    vtkTextMapper,
    vtkTextProperty
)

import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonComputationalGeometry import vtkParametricKuen
from vtkmodules.vtkCommonCore import (
    vtkCommand,
    vtkMath
)

from vtkmodules.vtkFiltersSources import vtkParametricFunctionSource
from vtkmodules.vtkInteractionWidgets import (
    vtkSliderRepresentation2D,
    vtkSliderWidget
)
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkProperty,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)


class System:
    def __init__(self, vtk_widget):
        # Initialize VTK rendering
        self.actors = []  # Store multiple actors for each loaded model
        self.selected_actor = None 
        self.is_model_move_enabled = False  # Flag to enable/disable model movement
        self.is_model_picked = False  # Flag to check if the model is picked
        self.is_model_color_enabled = False
        self.last_x = None
        self.last_y = None
        # Mouse position to track dragging
        self.last_x = None
        self.last_y = None
        self.original_colors = {}  # Initialize original_colors as an empty dictionary
        self.renderer = vtk.vtkRenderer()
        vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.renderer.SetBackground(0.0, 0.0, 0.00)  # Dark background
        vtk_widget.GetRenderWindow().Render()
        vtk_widget.Initialize()
        self.render_window = vtkRenderWindow()

        # Initialize interactor
        self.iren = vtk_widget.GetRenderWindow().GetInteractor()
        # Add a light
        self.light = vtk.vtkLight()
        self.renderer.AddLight(self.light)

        # Set default light properties
        self.light.SetIntensity(0.5)
        self.light.SetPosition(10, 10, 10)
        self.light.SetConeAngle(45)

        # Initialize grid floor and actor for shapes
        self.grid_actor = None
        self.grid_visible = False
        self.shape_actor = None
        self.add_grid_floor()

        # Set initial camera position
        self.set_camera_position()

        # Save the original interactor style
        self.original_interactor_style = self.iren.GetInteractorStyle()

        # Set up the pick observer to handle clicks
        self.iren.AddObserver("LeftButtonPressEvent", self.on_left_click)
        self.iren.AddObserver("MouseMoveEvent", self.on_mouse_move)

        # Create a picker for converting screen coordinates to world coordinates
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.001)

        # Set up interactor style to allow actor movement
        self.interactor_style = vtk.vtkInteractorStyleTrackballActor()
        self.iren.SetInteractorStyle(self.original_interactor_style)

        # Key press handling
        self.iren.AddObserver('KeyPressEvent', self.on_key_press)
        self.convex_points = []  # Add this line to initialize the list
    
    def add_shape(self, shape_type):
        # Create a new shape based on the type
        if shape_type == "sphere":
            source = vtk.vtkSphereSource()
            source.SetThetaResolution(50)
            source.SetPhiResolution(50)
            scale_factor = 3.0  # Scale factor to make the sphere larger
        elif shape_type == "cylinder":
            source = vtk.vtkCylinderSource()
            source.SetResolution(50)
            scale_factor = 2.5  # Scale factor to make the cylinder larger
        elif shape_type == "cube":
            source = vtk.vtkCubeSource()
            scale_factor = 2.0  # Scale factor to make the cube larger
        else:
            return  # Invalid shape type

        source.Update()

        # Create a mapper and actor for the shape
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())
        shape_actor = vtk.vtkActor()  # Create a new actor each time
        shape_actor.SetMapper(mapper)
        shape_actor.GetProperty().SetColor(1.0, 1.0, 1.0)  # Set default color to white

        # Set the scale to make the shape appear larger
        shape_actor.SetScale(scale_factor, scale_factor, scale_factor)

        # Add the shape actor to the renderer and add it to the actors list
        self.renderer.AddActor(shape_actor)
        self.actors.append(shape_actor)  # Append each new shape ac
        

    def close(self):
        """Close the scene by removing all renderers and resetting the view."""
        # Access the render window
        render_window = self.renderer.GetRenderWindow()

        # Get the collection of renderers
        renderer_collection = render_window.GetRenderers()
        renderer_collection.InitTraversal()

        # Remove all renderers one by one
        renderer = renderer_collection.GetNextItem()
        while renderer:
            render_window.RemoveRenderer(renderer)
            renderer = renderer_collection.GetNextItem()

        # Create and add a new default renderer
        self.renderer = vtk.vtkRenderer()
        render_window.AddRenderer(self.renderer)

        # Optionally reset the background color
        self.renderer.SetBackground(0.0, 0.0, 0.0)  # Black background

        # Add grid floor and reset camera position
        self.add_grid_floor()
        self.set_camera_position()

        # Render the updated scene
        render_window.Render()
        
    def load_model(self, file_path):
        # Determine the file extension and load the appropriate model
        file_extension = file_path.split('.')[-1].lower()

        if file_extension == 'ply':
            reader = vtk.vtkPLYReader()
        elif file_extension == 'obj':
            reader = vtk.vtkOBJReader()
        elif file_extension == 'stl':
            reader = vtk.vtkSTLReader()
        else:
            print("Unsupported File Format")
            return None  # Return None to indicate failure

        reader.SetFileName(file_path)
        reader.Update()

        # Check if the reader successfully loaded data
        poly_data = reader.GetOutput()
        if poly_data.GetNumberOfPoints() == 0:
            print("Failed to load model. No points found in the file.")
            return None  # Return None to indicate failure

        # Calculate the bounding box of the model
        bounds = poly_data.GetBounds()  # [xmin, xmax, ymin, ymax, zmin, zmax]
        x_size = bounds[1] - bounds[0]
        y_size = bounds[3] - bounds[2]
        z_size = bounds[5] - bounds[4]

        # Determine the largest dimension
        max_dimension = max(x_size, y_size, z_size)

        # Set the target size relative to the grid
        target_size = 10.0  # Adjust this value as needed to fit your grid

        # Calculate the scale factor
        scale_factor = target_size / max_dimension if max_dimension > 0 else 1.0

        # Apply the scaling transform
        transform = vtk.vtkTransform()
        transform.Scale(scale_factor, scale_factor, scale_factor)

        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetTransform(transform)
        transform_filter.SetInputData(poly_data)
        transform_filter.Update()

        # Create a mapper and actor for the transformed model
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(transform_filter.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # Store the original color of the actor
        self.original_colors[actor] = actor.GetProperty().GetColor()

        # Add the actor to the renderer
        self.renderer.AddActor(actor)
        self.actors.append(actor)  # Add actor to the actors list

        return poly_data  # Return the poly_data for further processing
    
   
    def start(self):
        """Start the VTK interactor."""
        self.iren.Initialize()
        self.iren.Start()

    def on_left_click(self, obj, event):
        """Handles the left click event for picking a model."""
        if not self.is_model_move_enabled:
            return  # Do nothing if model movement is disabled

        click_pos = self.iren.GetEventPosition()
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)
        picked_actor = self.picker.GetActor()

        if picked_actor in self.actors:
            # Deselect previously selected actor, if any
            if self.selected_actor:
                self.selected_actor.GetProperty().SetColor(1.0, 1.0, 1.0)  # Reset color to white

            # Select new actor
            if picked_actor != self.selected_actor:
                print("Model picked at:", self.picker.GetPickPosition())
                self.selected_actor = picked_actor
                self.selected_actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # Set color to red
                self.is_model_picked = True
            else:
                print("Model released at:", self.picker.GetPickPosition())
                self.is_model_picked = False
                self.selected_actor.GetProperty().SetColor(1.0, 1.0, 1.0)  # Reset color
                self.selected_actor = None

            # Update last mouse position
            self.last_x, self.last_y = click_pos if self.is_model_picked else (None, None)

    def on_mouse_move(self, obj, event):
        """Handle mouse move to drag the selected actor."""
        if not self.is_model_move_enabled:
            return  # Do nothing if model movement is disabled

        if self.is_model_picked and self.selected_actor:
            x, y = self.iren.GetEventPosition()
            self.picker.Pick(x, y, 0, self.renderer)
            picked_position = self.picker.GetPickPosition()

            if picked_position != (0, 0, 0):
                self.move_model(picked_position[0], picked_position[2])

            self.last_x, self.last_y = x, y

    def move_model(self, x, z):
        """Move the selected actor to the new (x, z) position."""
        if self.selected_actor:
            current_position = self.selected_actor.GetPosition()
            self.selected_actor.SetPosition(x, current_position[1], z)
            self.renderer.GetRenderWindow().Render()

    def toggle_model_movement(self):
        """Toggle model movement mode on or off."""
        self.is_model_move_enabled = not self.is_model_move_enabled

        if self.is_model_move_enabled:
            print("Model movement enabled.")
            # Enable movement interaction
            self.iren.SetInteractorStyle(self.interactor_style)
        else:
            print("Model movement disabled.")
            # Disable movement interaction
            self.iren.SetInteractorStyle(self.original_interactor_style)
            self.iren.Render()

    def toggle_model_color(self):
        """Toggle model color and texture editing mode on or off."""
        self.is_model_color_enabled = not self.is_model_color_enabled

        if self.is_model_color_enabled:
            print("Model color enabled. Select an anchor to modify its properties.")
            self.iren.SetInteractorStyle(self.interactor_style)
            self.setup_picking()
        else:
            print("Model color disabled.")
            self.iren.SetInteractorStyle(self.original_interactor_style)
            self.remove_picking()  # Disable picking
            self.selected_actor = None
            self.iren.Render()

    def setup_picking(self):
        """Setup picking functionality."""
        picker = vtk.vtkPropPicker()
        self.iren.SetPicker(picker)

        # Add observer for picking; store the observer ID for later removal
        self.picking_observer_id = self.iren.AddObserver("LeftButtonPressEvent", self.on_pick)

    def remove_picking(self):
        """Remove picking functionality."""
        if self.picking_observer_id is not None:
            self.iren.RemoveObserver(self.picking_observer_id)
            self.picking_observer_id = None

    def on_pick(self, obj, event):
        """Handle picking an object."""
        if not self.is_model_color_enabled:
            return  # Ignore picking if color editing is disabled

        picker = obj.GetPicker()
        click_pos = self.iren.GetEventPosition()
        picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)
        picked_actor = picker.GetActor()

        if picked_actor:
            print("Anchor selected.")
            self.selected_actor = picked_actor
        else:
            print("No anchor selected.")

    def change_color(self, color):
        """Apply color to the selected actor if one is picked."""
        if self.selected_actor:
            # Apply the new color to the selected actor
            self.selected_actor.GetProperty().SetColor(color.redF(), color.greenF(), color.blueF())
            print(f"Changed actor color to: {color.name()}")
            # Re-render after color change
            self.renderer.GetRenderWindow().Render()
        else:
            QMessageBox.information(None, "No Actor Selected", "Please pick an actor first before applying a color.")

    def apply_texture(self, texture_file):
        """Apply a texture to the selected actor if one is picked."""
        if not self.selected_actor:
            print("No Actor Selected. Please pick an actor first before applying a texture.")
            return

        # Load the image as a texture based on file extension
        texture = vtk.vtkTexture()
        extension = texture_file.split('.')[-1].lower()

        # Choose the correct reader based on the file extension
        if extension in ['jpg', 'jpeg']:
            texture_image_reader = vtk.vtkJPEGReader()
        elif extension == 'png':
            texture_image_reader = vtk.vtkPNGReader()
        elif extension == 'bmp':
            texture_image_reader = vtk.vtkBMPReader()
        else:
            print(f"Unsupported format .{extension} for textures.")
            return

        # Set the file name and update the reader
        texture_image_reader.SetFileName(texture_file)
        texture_image_reader.Update()

        # Check if the texture data was loaded successfully
        if not texture_image_reader.GetOutput():
            print("The texture file could not be loaded.")
            return

        # Set the texture to the actor
        texture.SetInputConnection(texture_image_reader.GetOutputPort())
        texture.InterpolateOn()  # Improves texture quality

        # Ensure the actor has texture coordinates
        if isinstance(self.selected_actor.GetMapper().GetInput(), vtk.vtkPolyData):
            # Check if the actor's polydata has texture coordinates
            polydata = self.selected_actor.GetMapper().GetInput()
            if not polydata.GetPointData().GetTCoords():
                # Add texture coordinates if they don't exist
                texture_mapper = vtk.vtkTextureMapToSphere()  # Use Sphere mapping; adjust as needed for your shape
                texture_mapper.SetInputData(polydata)
                texture_mapper.Update()
                self.selected_actor.GetMapper().SetInputData(texture_mapper.GetOutput())

        # Apply the texture to the selected actor
        self.selected_actor.SetTexture(texture)
        print(f"Applied texture: {texture_file}")

        # Re-render after applying texture
        self.renderer.GetRenderWindow().Render()


    def save_anchors_as_obj(self):
        """
        Save all anchors (actors) in the renderer as an OBJ file.
        This assumes the actors are stored in self.actors.
        """
        # Define a simpler path to save the file directly
        filename = "anchors.obj"  # Use a valid path

        if not self.actors:
            print("No actors to save!")
            return

        # Create a vtkAppendPolyData to append all actor's data
        append_filter = vtk.vtkAppendPolyData()

        for actor in self.actors:
            if actor.GetMapper() and actor.GetMapper().GetInput():
                append_filter.AddInputData(actor.GetMapper().GetInput())

        append_filter.Update()

        # Now write to OBJ file using vtkOBJWriter
        obj_writer = vtk.vtkOBJWriter()
        obj_writer.SetFileName(filename)
        obj_writer.SetInputData(append_filter.GetOutput())
        
        # Try writing and catch any potential errors
        try:
            obj_writer.Write()
            print(f"All anchors saved to {filename}.")
        except Exception as e:
            print(f"Error saving anchors: {e}")
            
    def set_camera_position(self):
        """Set the camera to a closer position to the object."""
        self.camera = vtk.vtkCamera()
        
        # Bring the camera closer to the object
        self.camera.SetPosition(5, 10, 5)  # Closer position; adjust as needed
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetViewUp(0, 1, 0)
        
        # Set this camera as the active camera
        self.renderer.SetActiveCamera(self.camera)
        
        # Apply slight zoom to bring the view even closer
        zoom_factor = 0.3  # Adjust as needed for more zoom (e.g., 1.1 for subtle, 1.5 for strong)
        self.camera.Dolly(zoom_factor)
        
        # Reset camera clipping range to fit the new view
        self.renderer.ResetCameraClippingRange()
        self.renderer.GetRenderWindow().Render()

    def create_box_actor(self):
        """Create a 3D box actor to move."""
        # Create a cube (3D box)
        cube = vtk.vtkCubeSource()
        cube.Update()

        # Map the cube geometry to an actor
        cube_mapper = vtk.vtkPolyDataMapper()
        cube_mapper.SetInputConnection(cube.GetOutputPort())
        
        self.shape_actor = vtk.vtkActor()
        self.shape_actor.SetMapper(cube_mapper)
        
        # Add the actor to the renderer
        self.renderer.AddActor(self.shape_actor)

        
    def add_grid_floor(self):
        """Add a grid floor for the scene (optional)."""
        # Create a grid using vtkPlaneSource
        grid = vtk.vtkPlaneSource()
        grid.SetXResolution(10)
        grid.SetYResolution(10)

        # Create a mapper for the grid
        grid_mapper = vtk.vtkPolyDataMapper()
        grid_mapper.SetInputConnection(grid.GetOutputPort())

        # Create an actor for the grid
        self.grid_actor = vtk.vtkActor()
        self.grid_actor.SetMapper(grid_mapper)
        
        # Set the grid's position in the scene
        self.grid_actor.SetPosition(0, 0, 0)  # You can adjust this position as needed

        # Disable the grid from being selected, interacted with, or manipulated
        self.grid_actor.GetProperty().SetVisibility(False)  # Hide initially if you prefer
        
        # Add the grid actor to the renderer
        self.renderer.AddActor(self.grid_actor)

        # Disable picking (interaction with the grid) by setting it as non-pickable
        self.grid_actor.GetPickable()  # Defaults to True, set it to False to prevent picking
        self.grid_actor.SetPickable(False)

    def toggle_grid(self):
        """Toggle the visibility of the grid."""
        if self.grid_visible:
            self.grid_actor.SetVisibility(False)
        else:
            self.grid_actor.SetVisibility(True)
            
        
        # Toggle the visibility flag
        self.grid_visible = not self.grid_visible


    def on_key_press(self, obj, event):
        """Handles key press events, specifically the 'q' key to toggle movement mode."""
        key = self.iren.GetKeySym()
        if key == 'q':  # Check if the 'q' key is pressed
            self.toggle_model_movement()


    def set_camera_position(self):
        """Set the camera to a closer position to the object."""
        self.camera = vtk.vtkCamera()
        
        # Bring the camera closer to the object
        self.camera.SetPosition(5, 10, 5)  # Closer position; adjust as needed
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetViewUp(0, 1, 0)
        
        # Set this camera as the active camera
        self.renderer.SetActiveCamera(self.camera)
        
        # Apply slight zoom to bring the view even closer
        zoom_factor = 0.3  # Adjust as needed for more zoom (e.g., 1.1 for subtle, 1.5 for strong)
        self.camera.Dolly(zoom_factor)
        
        # Reset camera clipping range to fit the new view
        self.renderer.ResetCameraClippingRange()
        self.renderer.GetRenderWindow().Render()

    def create_box_actor(self):
        """Create a 3D box actor to move."""
        # Create a cube (3D box)
        cube = vtk.vtkCubeSource()
        cube.Update()

        # Map the cube geometry to an actor
        cube_mapper = vtk.vtkPolyDataMapper()
        cube_mapper.SetInputConnection(cube.GetOutputPort())
        
        self.shape_actor = vtk.vtkActor()
        self.shape_actor.SetMapper(cube_mapper)
        
        # Add the actor to the renderer
        self.renderer.AddActor(self.shape_actor)

    def add_grid_floor(self):
        # Create a grid by drawing lines
        grid_size = 20
        grid_resolution = 20

        # Create points for the grid
        points = vtk.vtkPoints()
        for i in range(-grid_resolution, grid_resolution + 1):
            points.InsertNextPoint(i, 0, -grid_size)
            points.InsertNextPoint(i, 0, grid_size)
            points.InsertNextPoint(-grid_size, 0, i)
            points.InsertNextPoint(grid_size, 0, i)

        # Create polyline to connect the points
        lines = vtk.vtkCellArray()
        for i in range(0, points.GetNumberOfPoints(), 2):
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, i)
            line.GetPointIds().SetId(1, i + 1)
            lines.InsertNextCell(line)

        # Create polydata to store points and lines
        grid = vtk.vtkPolyData()
        grid.SetPoints(points)
        grid.SetLines(lines)

        # Create mapper and actor
        grid_mapper = vtk.vtkPolyDataMapper()
        grid_mapper.SetInputData(grid)
        self.grid_actor = vtk.vtkActor()
        self.grid_actor.SetMapper(grid_mapper)
        self.grid_actor.GetProperty().SetColor(0.5, 0.5, 0.5)  # Set color to gray
        self.grid_actor.GetProperty().SetLineWidth(1)
        self.grid_actor.GetProperty().SetOpacity(0.2)  # Set opacity to 20%

        # Add the grid actor to the renderer
        self.renderer.AddActor(self.grid_actor)

    def remove_grid(self):
        """Remove the grid from the renderer."""
        if self.grid_actor:
            self.renderer.RemoveActor(self.grid_actor)
            self.grid_actor = None


    def on_key_press(self, obj, event):
        """Handles key press events, specifically the 'q' key to toggle movement mode."""
        key = self.iren.GetKeySym()
        if key == 'q':  # Check if the 'q' key is pressed
            self.toggle_model_movement()

    def update_light_intensity(self, value):
        """Update the light intensity based on the slider value."""
        # Convert slider value (0-100) to range (0.0 - 1.0)
        intensity = value / 100.0
        self.light.SetIntensity(intensity)  
        self.renderer.GetRenderWindow().Render()  # Refresh the rendering

    def update_light_position(self, value):
        """Update the light position based on the X-axis slider."""
        # You might want to add sliders for Y and Z for better control
        x_position = value  # Update X based on the slider
        self.light.SetPosition(x_position, 5, 5)  # Y and Z fixed for simplicity
        self.renderer.GetRenderWindow().Render()  # Refresh the rendering

    def update_light_angle(self, value):
        """Update the light's cone angle based on the slider value."""
        # Map the slider value (0-100) to an angle (0-360 degrees)
        angle = value * 3.6  # Convert 0-100 range to 0-360 degrees
        self.light.SetConeAngle(angle)
        self.renderer.GetRenderWindow().Render()  # Refresh the rendering
        
    def add_models(self, model_type):
        import vtk
        if model_type == "Convex Point Set":
            # Clear any previous actors in the renderer
            self.renderer.RemoveAllViewProps()

            if not self.actors:
                print("No model loaded.")
                return

            # Get the model's points
            colors = vtk.vtkNamedColors()
            points = vtk.vtkPoints()

            # Iterate over all actors and extract their points
            for actor in self.actors:
                poly_data = actor.GetMapper().GetInput()
                model_points = poly_data.GetPoints()

                if model_points is None:
                    print("No points found in the model.")
                    continue

                num_points = model_points.GetNumberOfPoints()

                # Insert points into the vtkPoints object
                for i in range(num_points):
                    point = model_points.GetPoint(i)
                    points.InsertNextPoint(point)

            # Create a polydata object to hold the points
            poly_data = vtk.vtkPolyData()
            poly_data.SetPoints(points)

            # Create a sphere to represent each convex point
            sphere_source = vtk.vtkSphereSource()
            sphere_source.SetPhiResolution(4)  # Lower resolution for less smoothness
            sphere_source.SetThetaResolution(4)  # Lower resolution for less smoothness
            sphere_source.SetRadius(0.05)  # Radius of convex point

            # Create a mapper and actor for the convex points
            point_mapper = vtk.vtkGlyph3DMapper()
            point_mapper.SetInputData(poly_data)
            point_mapper.SetSourceConnection(sphere_source.GetOutputPort())

            point_actor = vtk.vtkActor()
            point_actor.SetMapper(point_mapper)
            point_actor.GetProperty().SetColor(colors.GetColor3d("Peacock"))

            # Add the point actor to the renderer
            self.renderer.AddActor(point_actor)

            # Create a "getah" (elastic band) around the convex points (grey color)
            # For this, you can use a line connecting the convex points
            line_source = vtk.vtkPolyLine()
            poly_line = vtk.vtkCellArray()

            # Here we're assuming we have a simple set of points; replace this with convex hull calculation
            num_points_in_vtk = points.GetNumberOfPoints()
            for i in range(num_points_in_vtk - 1):
                poly_line.InsertNextCell(2)
                poly_line.InsertCellPoint(i)
                poly_line.InsertCellPoint(i + 1)

            # Create a polydata object to hold the line
            line_poly_data = vtk.vtkPolyData()
            line_poly_data.SetPoints(points)
            line_poly_data.SetLines(poly_line)

            # Create a mapper for the line
            line_mapper = vtk.vtkPolyDataMapper()
            line_mapper.SetInputData(line_poly_data)

            # Create an actor for the line and set its color to grey
            line_actor = vtk.vtkActor()
            line_actor.SetMapper(line_mapper)
            line_actor.GetProperty().SetColor(colors.GetColor3d("Gray"))
            line_actor.GetProperty().SetLineWidth(0.1)  # Set the thickness of the line

            # Add the line actor to the renderer
            self.renderer.AddActor(line_actor)

            # # Set the background color to silver
            # self.renderer.SetBackground(colors.GetColor3d("Black"))

            # Reset the camera to fit the model
            self.renderer.ResetCamera()
            self.renderer.GetActiveCamera().Azimuth(210)
            self.renderer.GetActiveCamera().Elevation(30)
            self.renderer.ResetCameraClippingRange()

            # Render the windownder()
            
            self.renderer.GetRenderWindow().Render()
            
            
        elif model_type == "Platonic Solids":
            # Clear any previous actors in the renderer
            self.renderer.RemoveAllViewProps()

            import vtkmodules.vtkInteractionStyle
            import vtkmodules.vtkRenderingFreeType
            import vtkmodules.vtkRenderingOpenGL2
            from vtkmodules.vtkCommonColor import vtkNamedColors
            from vtkmodules.vtkFiltersSources import vtkPlatonicSolidSource
            from vtkmodules.vtkCommonCore import vtkLookupTable
            from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

            colors = vtkNamedColors()

            # Create the lookup table for coloring Platonic solids
            def get_platonic_lut():
                lut = vtkLookupTable()
                lut.SetNumberOfTableValues(20)
                lut.SetTableRange(0.0, 19.0)
                lut.Build()
                lut.SetTableValue(0, 0.1, 0.1, 0.1)
                lut.SetTableValue(1, 0, 0, 1)
                lut.SetTableValue(2, 0, 1, 0)
                lut.SetTableValue(3, 0, 1, 1)
                lut.SetTableValue(4, 1, 0, 0)
                lut.SetTableValue(5, 1, 0, 1)
                lut.SetTableValue(6, 1, 1, 0)
                lut.SetTableValue(7, 0.9, 0.7, 0.9)
                lut.SetTableValue(8, 0.5, 0.5, 0.5)
                lut.SetTableValue(9, 0.0, 0.0, 0.7)
                lut.SetTableValue(10, 0.5, 0.7, 0.5)
                lut.SetTableValue(11, 0, 0.7, 0.7)
                lut.SetTableValue(12, 0.7, 0, 0)
                lut.SetTableValue(13, 0.7, 0, 0.7)
                lut.SetTableValue(14, 0.7, 0.7, 0)
                lut.SetTableValue(15, 0, 0, 0.4)
                lut.SetTableValue(16, 0, 0.4, 0)
                lut.SetTableValue(17, 0, 0.4, 0.4)
                lut.SetTableValue(18, 0.4, 0, 0)
                lut.SetTableValue(19, 0.4, 0, 0.4)
                return lut

            # Data for Platonic solids
            platonic_solids_data = ['Tetrahedron', 'Cube', 'Octahedron', 'Icosahedron', 'Dodecahedron']

            lut = get_platonic_lut()

            # Create grid layout for multiple viewports
            grid_dimension_x = 3  # Number of columns
            grid_dimension_y = 2  # Number of rows
            renderer_size = 300
            self.renderer.GetRenderWindow().SetSize(renderer_size * grid_dimension_x, renderer_size * grid_dimension_y)

            for i, name in enumerate(platonic_solids_data):
                solid = vtkPlatonicSolidSource()
                solid.SetSolidType(i)

                mapper = vtkPolyDataMapper()
                mapper.SetInputConnection(solid.GetOutputPort())
                mapper.SetLookupTable(lut)
                mapper.SetScalarRange(0, 19)

                actor = vtkActor()
                actor.SetMapper(mapper)

                # Create a new renderer for each solid
                ren = vtk.vtkRenderer()
                ren.AddActor(actor)

                # Set up viewport layout (x_min, y_min, x_max, y_max)
                col = i % grid_dimension_x + 1
                row = i // grid_dimension_x
                viewport = [
                    float(col) / grid_dimension_x,
                    float(grid_dimension_y - (row + 1)) / grid_dimension_y,
                    float(col + 1) / grid_dimension_x,
                    float(grid_dimension_y - row) / grid_dimension_y
                ]
                ren.SetViewport(viewport)
                self.renderer.GetRenderWindow().AddRenderer(ren)

                # Reset camera for each renderer
                ren.ResetCamera()
                ren.GetActiveCamera().Azimuth(30)
                ren.GetActiveCamera().Elevation(30)
                ren.ResetCameraClippingRange()

            # Render all viewports
            self.renderer.GetRenderWindow().Render()
            
        elif model_type == "Parametric Kuen Demo":
            
            from vtkmodules.vtkCommonColor import vtkNamedColors
            from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkProperty
            from vtkmodules.vtkCommonComputationalGeometry import vtkParametricKuen
            from vtkmodules.vtkFiltersSources import vtkParametricFunctionSource
            from vtkmodules.vtkCommonColor import vtkNamedColors
            from vtkmodules.vtkCommonCore import vtkMath
            from vtkmodules.vtkInteractionWidgets import vtkSliderWidget, vtkSliderRepresentation2D


            # Define slider callback classes
            class SliderCallbackMinimumU:
                def __init__(self, parametric_function):
                    self.parametric_function = parametric_function

                def __call__(self, caller, event):
                    slider_widget = caller
                    value = slider_widget.GetRepresentation().GetValue()
                    if value > 0.9 * self.parametric_function.GetMaximumU():
                        value = 0.99 * self.parametric_function.GetMaximumU()
                        slider_widget.GetRepresentation().SetValue(value)
                    self.parametric_function.SetMinimumU(value)

            class SliderCallbackMaximumU:
                def __init__(self, parametric_function):
                    self.parametric_function = parametric_function

                def __call__(self, caller, event):
                    slider_widget = caller
                    value = slider_widget.GetRepresentation().GetValue()
                    if value < self.parametric_function.GetMinimumU() + 0.01:
                        value = self.parametric_function.GetMinimumU() + 0.01
                        slider_widget.GetRepresentation().SetValue(value)
                    self.parametric_function.SetMaximumU(value)
                    
            class SliderCallbackMinimumV():
                def __init__(self, kuen):
                    self.kuen = kuen

                def __call__(self, caller, ev):
                    sliderWidget = caller
                    value = sliderWidget.GetRepresentation().GetValue()
                    if value > 0.9 * self.kuen.GetMaximumV():
                        value = 0.99 * self.kuen.GetMaximumV()
                        sliderWidget.GetRepresentation().SetValue(value)
                    self.kuen.SetMinimumV(value)


            class SliderCallbackMaximumV():
                def __init__(self, kuen):
                    self.kuen = kuen

                def __call__(self, caller, ev):
                    sliderWidget = caller
                    value = sliderWidget.GetRepresentation().GetValue()
                    if value < self.kuen.GetMinimumV() + .01:
                        value = self.kuen.GetMinimumV() + .01
                        sliderWidget.GetRepresentation().SetValue(value)
                    self.kuen.SetMaximumV(value)


            # Clear any previous actors in the renderer
            self.renderer.RemoveAllViewProps()

            # Initialize colors and parametric surface
            colors = vtkNamedColors()
            # colors.SetColor('BkgColor', [26, 51, 102, 255])

            surface = vtkParametricKuen()
            source = vtkParametricFunctionSource()
            source.SetParametricFunction(surface)

            # Configure mapper and actor
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(source.GetOutputPort())

            actor = vtkActor()
            actor.SetMapper(mapper)
            back_property = vtkProperty()
            back_property.SetColor(colors.GetColor3d('Tomato'))
            actor.SetBackfaceProperty(back_property)
            actor.GetProperty().SetDiffuseColor(colors.GetColor3d('Banana'))
            actor.GetProperty().SetSpecular(0.5)
            actor.GetProperty().SetSpecularPower(20)

            # Add actor to the renderer
            self.renderer.AddActor(actor)
            self.renderer.ResetCamera()
            self.renderer.GetActiveCamera().Azimuth(30)
            self.renderer.GetActiveCamera().Elevation(-30)
            self.renderer.GetActiveCamera().Zoom(0.9)
            self.renderer.ResetCameraClippingRange()

            # Initialize the render window interactor if not already initialized
            if not hasattr(self, 'render_window_interactor'):
                self.render_window_interactor = vtk.vtkRenderWindowInteractor()
                self.render_window.SetInteractor(self.render_window_interactor)

            # Ensure the interactor is started for sliders
            interactor = self.render_window.GetInteractor()
            if interactor is None:
                raise RuntimeError("RenderWindowInteractor is not initialized.")

            # Slider configuration
            tube_width = 0.008
            slider_length = 0.008
            title_height = 0.02
            label_height = 0.02

            # Slider for Minimum U
            slider_rep_min_u = vtkSliderRepresentation2D()
            slider_rep_min_u.SetMinimumValue(-4.5)
            slider_rep_min_u.SetMaximumValue(4.5)
            slider_rep_min_u.SetValue(-4.5)
            slider_rep_min_u.SetTitleText('U min')
            slider_rep_min_u.GetPoint1Coordinate().SetValue(0.1, 0.1)
            slider_rep_min_u.GetPoint2Coordinate().SetValue(0.9, 0.1)

            slider_widget_min_u = vtkSliderWidget()
            slider_widget_min_u.SetInteractor(self.render_window_interactor)
            slider_widget_min_u.SetRepresentation(slider_rep_min_u)
            slider_widget_min_u.SetAnimationModeToAnimate()
            slider_widget_min_u.EnabledOn()
            slider_widget_min_u.AddObserver(vtkCommand.InteractionEvent, SliderCallbackMinimumU(surface))

            # Slider for Maximum U
            slider_rep_max_u = vtkSliderRepresentation2D()
            slider_rep_max_u.SetMinimumValue(-4.5)
            slider_rep_max_u.SetMaximumValue(4.5)
            slider_rep_max_u.SetValue(4.5)
            slider_rep_max_u.SetTitleText('U max')
            slider_rep_max_u.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
            slider_rep_max_u.GetPoint1Coordinate().SetValue(0.1, 0.9)
            slider_rep_max_u.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
            slider_rep_max_u.GetPoint2Coordinate().SetValue(0.9, 0.9)
            slider_rep_max_u.SetTubeWidth(tube_width)
            slider_rep_max_u.SetSliderLength(slider_length)
            slider_rep_max_u.SetTitleHeight(title_height)
            slider_rep_max_u.SetLabelHeight(label_height)

            slider_widget_max_u = vtkSliderWidget()
            slider_widget_max_u.SetInteractor(interactor)
            slider_widget_max_u.SetRepresentation(slider_rep_max_u)
            slider_widget_max_u.SetAnimationModeToAnimate()
            slider_widget_max_u.EnabledOn()
            slider_widget_max_u.AddObserver(vtkCommand.InteractionEvent, SliderCallbackMaximumU(surface))
            
            # Add V min slider
            slider_rep_min_v = vtkSliderRepresentation2D()
            slider_rep_min_v.SetMinimumValue(0.01)
            slider_rep_min_v.SetMaximumValue(vtkMath.Pi() - 0.05)
            slider_rep_min_v.SetValue(0.05)
            slider_rep_min_v.SetTitleText('V min')
            slider_rep_min_v.GetPoint1Coordinate().SetValue(0.1, 0.3)
            slider_rep_min_v.GetPoint2Coordinate().SetValue(0.9, 0.3)
            slider_rep_min_v.SetTubeWidth(0.008)
            slider_rep_min_v.SetSliderLength(0.008)
            slider_rep_min_v.SetTitleHeight(0.02)
            slider_rep_min_v.SetLabelHeight(0.02)

            slider_widget_min_v = vtkSliderWidget()
            slider_widget_min_v.SetInteractor(self.render_window_interactor)
            slider_widget_min_v.SetRepresentation(slider_rep_min_v)
            slider_widget_min_v.SetAnimationModeToAnimate()
            slider_widget_min_v.EnabledOn()
            slider_widget_min_v.AddObserver(vtkCommand.InteractionEvent, SliderCallbackMinimumV(surface))

            # Add V max slider
            slider_rep_max_v = vtkSliderRepresentation2D()
            slider_rep_max_v.SetMinimumValue(0.01)
            slider_rep_max_v.SetMaximumValue(vtkMath.Pi() - 0.05)
            slider_rep_max_v.SetValue(vtkMath.Pi() - 0.05)
            slider_rep_max_v.SetTitleText('V max')
            slider_rep_max_v.GetPoint1Coordinate().SetValue(0.1, 0.4)
            slider_rep_max_v.GetPoint2Coordinate().SetValue(0.9, 0.4)
            slider_rep_max_v.SetTubeWidth(0.008)
            slider_rep_max_v.SetSliderLength(0.008)
            slider_rep_max_v.SetTitleHeight(0.02)
            slider_rep_max_v.SetLabelHeight(0.02)

            slider_widget_max_v = vtkSliderWidget()
            slider_widget_max_v.SetInteractor(self.render_window_interactor)
            slider_widget_max_v.SetRepresentation(slider_rep_max_v)
            slider_widget_max_v.SetAnimationModeToAnimate()
            slider_widget_max_v.EnabledOn()
            slider_widget_max_v.AddObserver(vtkCommand.InteractionEvent, SliderCallbackMaximumV(surface))


            # Set initial parametric function parameters
            surface.SetMinimumU(-4.5)
            surface.SetMaximumU(4.5)
            surface.SetMinimumV(0.05)
            surface.SetMaximumV(vtkMath.Pi() - 0.05)

            # Render the window
            self.renderer.GetRenderWindow().Render()
            
        elif model_type == "Lorenz":
            import vtkmodules.all as vtk
            from vtkmodules.vtkCommonColor import vtkNamedColors
            from vtkmodules.vtkCommonCore import vtkMinimalStandardRandomSequence
            from vtkmodules.vtkCommonDataModel import vtkStructuredPoints
            from vtkmodules.vtkFiltersCore import vtkContourFilter
            from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper
            
            colors = vtkNamedColors()
            
            # Lorenz parameters
            Pr = 10.0
            b = 2.667
            r = 28.0
            h = 0.01
            resolution = 200
            iterations = 3000000
            xmin, xmax = -30.0, 30.0
            ymin, ymax = -30.0, 30.0
            zmin, zmax = -10.0, 60.0
            
            # Resolution scaling
            xIncr = resolution / (xmax - xmin)
            yIncr = resolution / (ymax - ymin)
            zIncr = resolution / (zmax - zmin)
            
            # Random starting point
            randomSequence = vtkMinimalStandardRandomSequence()
            randomSequence.SetSeed(8775070)
            x = randomSequence.GetRangeValue(xmin, xmax)
            randomSequence.Next()
            y = randomSequence.GetRangeValue(ymin, ymax)
            randomSequence.Next()
            z = randomSequence.GetRangeValue(zmin, zmax)
            randomSequence.Next()
            
            # Initialize scalars for Lorenz volume
            num_pts = resolution ** 3
            scalars = vtk.vtkShortArray()
            scalars.SetNumberOfValues(num_pts)
            scalars.Fill(0)
            
            # Generate Lorenz attractor data
            for _ in range(iterations):
                xx = x + h * Pr * (y - x)
                yy = y + h * (x * (r - z) - y)
                zz = z + h * (x * y - b * z)
                x, y, z = xx, yy, zz
                
                # Map Lorenz points to scalar field
                if xmin <= x <= xmax and ymin <= y <= ymax and zmin <= z <= zmax:
                    i = int((x - xmin) * xIncr)
                    j = int((y - ymin) * yIncr)
                    k = int((z - zmin) * zIncr)
                    index = i + j * resolution + k * resolution ** 2
                    scalars.SetValue(index, scalars.GetValue(index) + 1)
            
            # Create volume from scalar data
            volume = vtkStructuredPoints()
            volume.SetDimensions(resolution, resolution, resolution)
            volume.SetOrigin(xmin, ymin, zmin)
            volume.SetSpacing((xmax - xmin) / resolution, (ymax - ymin) / resolution, (zmax - zmin) / resolution)
            volume.GetPointData().SetScalars(scalars)
            
            # Contour filter to extract isosurface
            contour = vtkContourFilter()
            contour.SetInputData(volume)
            contour.SetValue(0, 50)  # Adjust contour value as needed
            
            # Mapper and actor for visualization
            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(contour.GetOutputPort())
            mapper.ScalarVisibilityOff()
            
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(colors.GetColor3d('DodgerBlue'))
            
            # Add actor to renderer
            self.renderer.RemoveAllViewProps()
            self.renderer.AddActor(actor)
            self.renderer.SetBackground(colors.GetColor3d('Black'))
            
            # Camera configuration
            camera = self.renderer.GetActiveCamera()
            camera.SetPosition(-67, -25, 63)
            camera.SetFocalPoint(3, -4, 29)
            camera.SetViewUp(-0.23, 0.96, 0.12)
            self.renderer.ResetCameraClippingRange()
            
            # Render the scene
            self.renderer.GetRenderWindow().Render()
            
        elif model_type == "Spring":
            from vtkmodules.vtkCommonColor import vtkNamedColors
            from vtkmodules.vtkCommonCore import vtkPoints
            from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
            from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
            from vtkmodules.vtkFiltersModeling import vtkRotationalExtrusionFilter
            from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

            colors = vtkNamedColors()

            # Create the spring profile (a circle).
            points = vtkPoints()
            points.InsertPoint(0, 1.0, 0.0, 0.0)
            points.InsertPoint(1, 1.0732, 0.0, -0.1768)
            points.InsertPoint(2, 1.25, 0.0, -0.25)
            points.InsertPoint(3, 1.4268, 0.0, -0.1768)
            points.InsertPoint(4, 1.5, 0.0, 0.00)
            points.InsertPoint(5, 1.4268, 0.0, 0.1768)
            points.InsertPoint(6, 1.25, 0.0, 0.25)
            points.InsertPoint(7, 1.0732, 0.0, 0.1768)

            poly = vtkCellArray()
            poly.InsertNextCell(8)  # The number of points.
            for i in range(8):
                poly.InsertCellPoint(i)

            profile = vtkPolyData()
            profile.SetPoints(points)
            profile.SetPolys(poly)

            # Extrude the profile to make a spring.
            extrude = vtkRotationalExtrusionFilter()
            extrude.SetInputData(profile)
            extrude.SetResolution(360)
            extrude.SetTranslation(6)
            extrude.SetDeltaRadius(1.0)
            extrude.SetAngle(2160.0)  # Six revolutions

            normals = vtkPolyDataNormals()
            normals.SetInputConnection(extrude.GetOutputPort())
            normals.SetFeatureAngle(60)

            mapper = vtkPolyDataMapper()
            mapper.SetInputConnection(normals.GetOutputPort())

            spring = vtkActor()
            spring.SetMapper(mapper)
            spring.GetProperty().SetColor(colors.GetColor3d("PowderBlue"))
            spring.GetProperty().SetDiffuse(0.7)
            spring.GetProperty().SetSpecular(0.4)
            spring.GetProperty().SetSpecularPower(20)
            spring.GetProperty().BackfaceCullingOn()

            # Clear previous actors
            self.renderer.RemoveAllViewProps()

            # Add the spring actor to the shared renderer
            self.renderer.AddActor(spring)

            # Reset the camera and render the scene
            self.renderer.ResetCamera()
            self.renderer.GetActiveCamera().Azimuth(90)
            self.renderer.GetRenderWindow().Render()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window settings
        self.setWindowTitle("Blender")
        self.setGeometry(100, 100, 1000, 630)
        self.setWindowIcon(QIcon("blender.svg"))
      
        # Create the VTK render window interactor
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.setCentralWidget(self.vtkWidget)
        # Initialize the system (VTK logic)
        self.system = System(self.vtkWidget)

        # Set up layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.vtkWidget)
        central_widget = QWidget(self)
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        # Initialize toolbar
        self.create_toolbar()
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c2f38;
            }
            QToolBar {
                background-color: #000000;
                border: none;
            }
        """)
        
        self.leftframe = QFrame(self)
        self.leftframe.setStyleSheet("background-color: rgb(30, 30, 30); border: 1px solid rgba(255, 255, 255, 0.1);")
        self.leftframe.setFixedSize(200, 180)
        self.update_leftframe_position()

        self.leftframe2 = QFrame(self)
        self.leftframe2.setStyleSheet("background-color: rgb(30, 30, 30); border: 1px solid rgba(255, 255, 255, 0.1);")
        self.leftframe2.setFixedSize(200, 350)
        self.update_leftframe2_position()
        
        self.rightframe = QFrame(self)
        self.rightframe.setStyleSheet("background-color: rgb(30, 30, 30); border: 1px solid rgba(255, 255, 255, 0.1);border-radius:10px")
        self.rightframe.setFixedSize(60, 160)
        self.update_rightframe_position()
        
        self.setup_sliders()
        # Create a horizontal layout for the buttons with minimal spacing
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)  # Minimal gap between buttons
        button_layout.setContentsMargins(0, 0, 0, 0)  # No margins to align with top

        # Create three buttons and set icons (replace icon paths if needed)
        button1 = QPushButton()
        button1.setStyleSheet("""
        QPushButton {
            background-color: rgb(50, 50, 50);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            padding: 10px 15px;
            color: white;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: rgb(255, 159, 10);  /* Change color on hover */
            border: 1px solid rgba(255, 255, 255, 0.4);  /* Subtle border change */
        }
    """)

        button1.setIcon(QIcon("help.svg"))  # Replace with actual icon path

        button2 = QPushButton()
        button2.setStyleSheet("background-color: rgb(50, 80, 105);")
        button2.setStyleSheet("""
        QPushButton {
            background-color: rgb(50, 50, 50);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            padding: 10px 15px;
            color: white;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: rgb(255, 159, 10);  /* Change color on hover */
            border: 1px solid rgba(255, 255, 255, 0.4);  /* Subtle border change */
        }
    """)       
        button2.setIcon(QIcon("grid.svg"))
        button2.clicked.connect(self.system.toggle_grid)


        button3 = QPushButton()
        button3.setStyleSheet("""
        QPushButton {
            background-color: rgb(50, 50, 50);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            padding: 10px 15px;
            color: white;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: rgb(255, 159, 10);  /* Change color on hover */
            border: 1px solid rgba(255, 255, 255, 0.4);  /* Subtle border change */
        }
    """)   
        button3.setIcon(QIcon("save.svg"))
        button3.clicked.connect(self.system.save_anchors_as_obj)


        # Set the size for each button
        button1.setFixedSize(50, 25)
        button2.setFixedSize(50, 25)
        button3.setFixedSize(50, 25)

        # Add the buttons to the horizontal layout
        button_layout.addWidget(button1)
        button_layout.addWidget(button2)
        button_layout.addWidget(button3)

        self.white_box = QFrame(self)
        self.white_box.setFrameShape(QFrame.StyledPanel)
        self.white_box.setFrameShadow(QFrame.Raised)

        self.white_box_layout = QVBoxLayout(self.white_box)
        self.white_box_layout.setContentsMargins(10, 10, 10, 10)  # Apply margins
        self.white_box_layout.setSpacing(10)

        # Set up the label
        self.stats_label = QLabel(self.white_box)
        self.stats_label.setWordWrap(True)  # Enable text wrapping
        self.stats_label.setAlignment(Qt.AlignCenter)  # Center align the text

        # Apply font size and style
        font = self.stats_label.font()
        font.setPointSize(10)  # Set the font size to 14 (adjust as needed)
        font.setBold(True)  # Make the text bold (optional)
        self.stats_label.setFont(font)
        
        # Set white font color using a stylesheet
        self.stats_label.setStyleSheet("color: white;")


        # Add the label to the layout
        self.white_box_layout.addWidget(self.stats_label)

        # Create the main vertical layout for the leftframe2 (define it only once)
        main_layout = QVBoxLayout(self.leftframe2)
        main_layout.setContentsMargins(20, 20, 20, 0)  # Margin on all sides of layout (left, top, right)
        main_layout.setSpacing(20)  # Minimal vertical spacing
        main_layout.setAlignment(Qt.AlignTop)  # Align layout to the top of leftframe2

        # Add button layout and white box to the main layout
        main_layout.addLayout(button_layout)  # Add the button layout at the very top
        main_layout.addWidget(self.white_box)  # Add the white box below the buttons

        # Set the main layout to the frame
        self.leftframe2.setLayout(main_layout)

            # Align the button layout to the top and center horizontally
        button_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Ensure the SVG file paths are correct
        icon_path_a = r"move.svg"   # Initial icon
        icon_path_b = r"moveB.svg"  # Icon to switch to on click

        # Create a button with an icon instead of text
        self.toggle_button = QPushButton(self.rightframe)
        self.toggle_button.setIcon(QIcon(icon_path_a))
        self.toggle_button.setGeometry(10, 10, 40, 40)  # Adjust the size to match the icon
        self.toggle_button.setIconSize(QSize(32, 32))  # Adjust icon size as needed
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(50, 50, 50);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgb(255, 159, 10); /* Modern orange color */
            }
        """)

        # Track the icon state
        self.toggle_icon_state = True  # True means showing icon_path_a for toggle_button

        # Define a function to toggle the icon for toggle_button
        def toggle_icon_a():
            if self.toggle_icon_state:
                self.toggle_button.setIcon(QIcon(icon_path_b))
            else:
                self.toggle_button.setIcon(QIcon(icon_path_a))
            self.toggle_icon_state = not self.toggle_icon_state  # Toggle the state

        # Connect the button click to the toggle function for toggle_button
        self.toggle_button.clicked.connect(toggle_icon_a)
        self.toggle_button.clicked.connect(self.system.toggle_model_movement)

        # Map button setup
        icon_patha = r"EYE.svg"   # Initial icon
        icon_pathb = r"EYEb.svg"  # Icon to switch to on click

        # Create a button with an icon instead of text
        self.map_button = QPushButton(self.rightframe)
        self.map_button.setIcon(QIcon(icon_patha))
        self.map_button.setGeometry(10, 60, 40, 40)  # Adjust the size to match the icon
        self.map_button.setIconSize(QSize(32, 32))  # Adjust icon size as needed
        self.map_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(50, 50, 50);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgb(255, 159, 10); /* Modern orange color */
            }
        """)

        # Track the icon state for map_button
        self.map_icon_state = True  # True means showing icon_patha for map_button

        # Define a function to toggle the icon for map_button
        def toggle_icon_b():
            if self.map_icon_state:
                self.map_button.setIcon(QIcon(icon_pathb))
            else:
                self.map_button.setIcon(QIcon(icon_patha))
            self.map_icon_state = not self.map_icon_state  # Toggle the state

        # Connect the button click to the toggle function for map_button
        self.map_button.clicked.connect(toggle_icon_b)
        self.map_button.clicked.connect(self.system.toggle_model_color)
        # Close button setup
        close_icon_path = r"close.svg"  # Icon for the close button

        # Create a close button with an icon
        self.close_button = QPushButton(self.rightframe)
        self.close_button.setIcon(QIcon(close_icon_path))
        self.close_button.setGeometry(10, 110, 40, 40)  # Adjust position below toggle_button
        self.close_button.setIconSize(QSize(32, 32))
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(50, 50, 50);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgb(255, 80, 80);
            }
        """)
        self.close_button.clicked.connect(self.system.close)

    def update_leftframe_position(self):
        """Update the position of the left frame."""
        x_pos = 15  # Fixed left position
        y_pos = 38  # Fixed top position
        self.leftframe.setGeometry(x_pos, y_pos, self.leftframe.width(), self.leftframe.height())

    def update_leftframe2_position(self):
        """Update the position of the second left frame."""
        x_pos = 15  # Fixed left position
        y_pos = self.leftframe.geometry().bottom() + 10  # Place 10px below the first frame
        self.leftframe2.setGeometry(x_pos, y_pos, self.leftframe2.width(), self.leftframe2.height())

    def update_rightframe_position(self):
        """Update the position of the right frame."""
        x_pos = self.width() - self.rightframe.width() - 15  # 15px from the right edge
        y_pos = 38  # Fixed y position (can be adjusted)
        self.rightframe.setGeometry(x_pos, y_pos, self.rightframe.width(), self.rightframe.height())
  
    def setup_sliders(self):
        # Layout for the sliders
        slider_layout = QVBoxLayout(self.leftframe)

        # Horizontal layout for the "Lighting" label and icon
        label_icon_layout = QHBoxLayout()

        # Create the label for lighting
        lightlabel = QLabel("Lighting", self.leftframe)
        lightlabel.setStyleSheet("""
            QLabel {
                color: white;                       /* White text color */
                border: none;                       /* Removes the border */
                padding: 1px 1px;                   /* Adds padding inside the label */
                font-size: 12px;                    /* Adjust font size */
            }
        """)

        # Add an SVG icon (or use a QPixmap for light)
        light_icon = QLabel(self.leftframe)
        pixmap = QPixmap(r"light.svg")  # Replace with your light icon path
        light_icon.setPixmap(pixmap)
        light_icon.setAlignment(Qt.AlignLeft)  # Align the icon to the left
        light_icon.setFixedSize(20, 20)  # Set the fixed size for the icon
        light_icon.setScaledContents(True)  # Ensure the contents scale to the fixed size

        # Add the label and icon to the horizontal layout
        label_icon_layout.addWidget(light_icon)
        label_icon_layout.addWidget(lightlabel)

        # Add the horizontal layout to the vertical layout
        slider_layout.addLayout(label_icon_layout)

        # Slider stylesheet
        slider_style = """
        QSlider::handle:horizontal {
            background: rgb(70, 70, 70);
            border-radius: 4px;
            width: 14px;  /* Adjust width for a more visible handle */
            height: 14px; /* Adjust height for a more visible handle */
            margin: -6px 0;  /* Center the handle on the groove */
        }
        QSlider::handle:horizontal:hover {
            background: rgb(100, 100, 100);  /* Lighter color on hover */
        }
        QSlider::handle:horizontal:pressed {
            background: rgb(50, 50, 50);  /* Darker color when pressed */
        }
        QSlider::groove:horizontal {
            background: rgb(45, 45, 45);
            height: 6px;  /* Slightly increased height for better visibility */
            border-radius: 2px;
        }
        QSlider::sub-page:horizontal {
            background: rgb(255, 159, 10);  /* Highlighted part of the slider */
            border-radius: 2px;
        }
        QSlider::add-page:horizontal {
            background: rgb(45, 45, 45);  /* Unfilled part of the slider */
            border-radius: 2px;
        }
    """


        # Slider for Light Intensity
        intensity_label = QLabel("Intensity", self.leftframe)
        intensity_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 12px;")
        slider_layout.addWidget(intensity_label)

        self.intensity_slider = QSlider(Qt.Horizontal, self.leftframe)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(50)  # Default value
        self.intensity_slider.setStyleSheet(slider_style)
        self.intensity_slider.valueChanged.connect(self.system.update_light_intensity)
        slider_layout.addWidget(self.intensity_slider)

        # Slider for Light Position (X-axis)
        position_label = QLabel("Position X", self.leftframe)
        position_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 12px;")
        slider_layout.addWidget(position_label)

        self.position_slider = QSlider(Qt.Horizontal, self.leftframe)
        self.position_slider.setRange(-100, 100)
        self.position_slider.setValue(0)  # Default value
        self.position_slider.setStyleSheet(slider_style)
        self.position_slider.valueChanged.connect(self.system.update_light_position)
        slider_layout.addWidget(self.position_slider)

        # Slider for Light Angle
        angle_label = QLabel("Angle", self.leftframe)
        angle_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 12px;")
        slider_layout.addWidget(angle_label)

        self.angle_slider = QSlider(Qt.Horizontal, self.leftframe)
        self.angle_slider.setRange(0, 180)
        self.angle_slider.setValue(45)  # Default value
        self.angle_slider.setStyleSheet(slider_style)
        self.angle_slider.valueChanged.connect(self.system.update_light_angle)
        slider_layout.addWidget(self.angle_slider)

        # Set the layout for the frame
        self.leftframe.setLayout(slider_layout)

    def create_toolbar(self):
        """Create a toolbar with File, Add, and View buttons."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # File button
        file_button = QPushButton("File")
        file_button.setStyleSheet(self.button_style())
        file_button.clicked.connect(self.show_file_menu)
        toolbar.addWidget(file_button)
        
        # Model button
        model_button = QPushButton("Models")
        model_button.setStyleSheet(self.button_style())
        model_button.clicked.connect(self.show_model_menu)
        toolbar.addWidget(model_button)

        # Add button
        shape_button = QPushButton("Shape")
        shape_button.setStyleSheet(self.button_style())
        shape_button.clicked.connect(self.show_shape_menu)
        toolbar.addWidget(shape_button)

        # View button
        view_button = QPushButton("View")
        view_button.setStyleSheet(self.button_style())
        view_button.clicked.connect(self.show_view_menu)
        toolbar.addWidget(view_button)

    def show_file_menu(self):
        # Create a menu for object selection
        menu = QMenu()

        # Apply dark mode background to the menu
        menu.setStyleSheet("""
            QMenu {
                background-color: #2e2e2e;  /* Dark background */
                color: white;  /* White text */
            }
            QMenu::item {
                background-color: #3e3e3e;  /* Darker background for items */
                color: white;  /* White text for items */
            }
            QMenu::item:selected {
                background-color: #4e4e4e;  /* Lighter background for selected items */
                color: white;  /* White text for selected items */
            }
        """)
        
        """Show File menu with Open and Save options."""
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.system.save_anchors_as_obj)
        menu.addAction(save_action)

        # Display the menu below the File button
        menu.exec(QCursor.pos())
        
    def show_model_menu(self):
        menu = QMenu()
        # Apply dark mode background to the menu
        menu.setStyleSheet("""
            QMenu {
                background-color: #2e2e2e;  /* Dark background */
                color: white;  /* White text */
            }
            QMenu::item {
                background-color: #3e3e3e;  /* Darker background for items */
                color: white;  /* White text for items */
            }
            QMenu::item:selected {
                background-color: #4e4e4e;  /* Lighter background for selected items */
                color: white;  /* White text for selected items */
            }
        """)
        
        """Show Model menu with Models options."""
        cell_format_action = QAction("Cell Format", self)
        cell_format_action.triggered.connect(lambda: self.system.add_models("Convex Point Set"))
        menu.addAction(cell_format_action)
        
        source_format_action = QAction("Source Format", self)
        source_format_action.triggered.connect(lambda: self.system.add_models("Platonic Solids"))
        menu.addAction(source_format_action)
        
        parametric_object_action = QAction("Parametric Object", self)
        parametric_object_action.triggered.connect(lambda: self.system.add_models("Parametric Kuen Demo"))
        menu.addAction(parametric_object_action)
        
        impfunction_isosurface_action = QAction("Implicit Function and Iso-surfaces", self)
        impfunction_isosurface_action.triggered.connect(lambda: self.system.add_models("Lorenz"))
        menu.addAction(impfunction_isosurface_action)
        
        functional_3d_action = QAction("Functional 3D Data", self)
        functional_3d_action.triggered.connect(lambda: self.system.add_models("Spring"))
        menu.addAction(functional_3d_action)
        
        # Display the menu below the Add button
        menu.exec(QCursor.pos())
        
    

    def show_shape_menu(self):
        
        menu = QMenu()
        # Apply dark mode background to the menu
        menu.setStyleSheet("""
            QMenu {
                background-color: #2e2e2e;  /* Dark background */
                color: white;  /* White text */
            }
            QMenu::item {
                background-color: #3e3e3e;  /* Darker background for items */
                color: white;  /* White text for items */
            }
            QMenu::item:selected {
                background-color: #4e4e4e;  /* Lighter background for selected items */
                color: white;  /* White text for selected items */
            }
        """)
        
        """Show Shapes menu with Add options."""
        sphere_action = QAction("Add Sphere", self)
        sphere_action.triggered.connect(lambda: self.system.add_shape("sphere"))
        menu.addAction(sphere_action)

        cylinder_action = QAction("Add Cylinder", self)
        cylinder_action.triggered.connect(lambda: self.system.add_shape("cylinder"))
        menu.addAction(cylinder_action)

        cube_action = QAction("Add Cube", self)
        cube_action.triggered.connect(lambda: self.system.add_shape("cube"))
        menu.addAction(cube_action)

        # Display the menu below the Add button
        menu.exec(QCursor.pos())

    def show_view_menu(self):
        
        menu = QMenu()
        # Apply dark mode background to the menu
        menu.setStyleSheet("""
            QMenu {
                background-color: #2e2e2e;  /* Dark background */
                color: white;  /* White text */
            }
            QMenu::item {
                background-color: #3e3e3e;  /* Darker background for items */
                color: white;  /* White text for items */
            }
            QMenu::item:selected {
                background-color: #4e4e4e;  /* Lighter background for selected items */
                color: white;  /* White text for selected items */
            }
        """)
        """Show View menu with Color and Texture options."""
        
        change_color_action = QAction("Change Color", self)
        change_color_action.triggered.connect(self.open_color_picker)
        menu.addAction(change_color_action)

        apply_texture_action = QAction("Apply Texture", self)
        apply_texture_action.triggered.connect(self.open_texture_picker)
        menu.addAction(apply_texture_action)

        # Display the menu below the View button
        menu.exec(QCursor.pos())

    def button_style(self):
        """Return a modern Blender-like style for toolbar buttons."""
        return """
        QPushButton {
            background-color: rgb(10, 10, 10); /* Neutral dark gray */
            padding: 6px 10px; /* Compact padding */
            color: white;
            font-size: 11px; /* Small font for modern look */
            font-family: 'Segoe UI', sans-serif; /* Clean font style */
        }
        QPushButton:hover {
            background-color: rgb(66, 66, 66); /* Slightly lighter gray on hover */
            border: 1px solid rgb(80, 80, 80); /* Highlight border subtly */
        }
        QPushButton:pressed {
            background-color: rgb(46, 46, 46); /* Darker gray when pressed */
            border: 1px solid rgb(90, 90, 90); /* Pressed border effect */
        }
        QPushButton:disabled {
            background-color: rgb(45, 45, 45); /* Dimmed for disabled state */
            border: 1px solid rgb(50, 50, 50); /* Muted border */
            color: rgb(120, 120, 120); /* Muted text color */
        }
        """

    def open_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.system.change_color(color)
        
    def open_texture_picker(self):
        # Open file dialog to select an image file
        texture_file, _ = QFileDialog.getOpenFileName(self, "Open Texture File", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if texture_file:
            self.system.apply_texture(texture_file)



    def open_file(self):
        """Open a 3D model file using a file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open 3D Model", "", "3D Files (*.ply *.obj *.stl);;All Files (*)"
        )

        if file_path:
            # Call load_model method in System class
            poly_data = self.system.load_model(file_path)  # Get poly_data on success
            if not poly_data:
                QMessageBox.warning(self, "Error", "Failed to load the model.")
                return

            # Successfully loaded model, update the render window
            self.vtkWidget.GetRenderWindow().Render()

            # Get model statistics
            # Set up the model statistics
            num_vertices = poly_data.GetNumberOfPoints()
            num_polygons = poly_data.GetNumberOfPolys()
            num_lines = poly_data.GetNumberOfLines()
            num_cells = poly_data.GetNumberOfCells()
            num_triangles = poly_data.GetNumberOfPolys() if poly_data.GetPolys() else 0

            # Prepare statistics text
            stats_text = (
                f"Model Statistics:\n\n"
                f"Vertices: {num_vertices}\n"
                f"Polygons: {num_polygons}\n"
                f"Lines: {num_lines}\n"
                f"Cells: {num_cells}\n"
                f"Triangles: {num_triangles}"
            )

            # Set up the label with desired style
            self.stats_label.setAlignment(QtCore.Qt.AlignLeft)  # Align text to the left
            self.stats_label.setText(stats_text)

            # Style the label with a modern and clean appearance
            self.stats_label.setStyleSheet("""
                QLabel {
                    background-color: #232323;  /* Dark background color */
                    border: 1px solid #444444;  /* Subtle darker border */
                    padding: 9px;  /* Padding for better readability */
                    font-family: 'Arial', sans-serif;  /* Simple and modern font */
                    font-size: 12px;  /* Small but readable font size */
                    color: grey;  /* Light gray text for good contrast */
                }
            """)

    def resizeEvent(self, event):
        """Handle the resizing of the main window."""
        # Update VTK widget size
        self.vtkWidget.GetRenderWindow().SetSize(event.size().width(), event.size().height())
        self.vtkWidget.GetRenderWindow().Render()

        # Update the positions and sizes of the frames
        self.update_leftframe_position()
        self.update_leftframe2_position()
        self.update_rightframe_position()

        super().resizeEvent(event)  # Call the base class resizeEvent to ensure proper handling
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()  # Close the window if ESC is pressed
        
# Main Execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    