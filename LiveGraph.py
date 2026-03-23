import matplotlib.pyplot as plt
import time
import csv
import os

class LiveGraph:
    def __init__(self, title="Live Graph", xlabel="X", ylabel="Y", max_points=200000, fileName=""):
        self.fileName = fileName
        self.max_points = max_points
        self.data = {}  # Dictionary to store {line_name: (x_data, y_data)}
        self.lines = {}  # Dictionary to store {line_name: Line2D object}
        self.derived_lines = {}
        self.rolling_averages = {}  # {avg_line_name: (source_line_name, window)}

        
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel

        self.fig, self.ax = plt.subplots()
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)

        self.fig.show()
        self.last_update = time.time()

    def add_line(self, name, colour=None):
        #Create a new line for the graph
        self.data[name] = ([], [])
        line, = self.ax.plot([], [], label=name, lw=2, color=colour)
        self.lines[name] = line
        self.ax.legend()

    def push(self, name, x, y):
        #Push a new data point onto a named line
        if name not in self.data:
            raise ValueError(f"Line '{name}' has not been added. Call add_line(name) first.")

        x_data, y_data = self.data[name]
        x_data.append(x)
        y_data.append(y)

        if len(x_data) > self.max_points:
            x_data.pop(0)
            y_data.pop(0)

        # Update any derived lines that depend on this one
        for derived_name, (source_name, window) in self.derived_lines.items():
            if source_name != name:
                continue  # Only update if the source was pushed

            src_x, src_y = self.data[source_name]
            dx, dy = self.data[derived_name]

            if len(src_x) >= window + 1:
                delta_x = src_x[-1] - src_x[-1 - window]
                delta_y = src_y[-1] - src_y[-1 - window]
                if delta_x != 0:
                    dx.append(src_x[-1])
                    dy.append(delta_y / delta_x)

                    if len(dx) > self.max_points:
                        dx.pop(0)
                        dy.pop(0)

    #Update the render of the graph - called within a loop
    def update(self):
        now = time.time()
        if now - self.last_update >= 0.1:  # 10 updates per second
            for name, line in self.lines.items():
                x_data, y_data = self.data[name]
                line.set_data(x_data, y_data)

            self.ax.relim()
            self.ax.autoscale_view()
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            self.last_update = now

    #Save graph and data as a csv file
    def save(self):
        # Ensure the folder exists
        os.makedirs(self.fileName, exist_ok=True)

        # Save the graph image
        image_path = os.path.join(self.fileName, f"{self.title}.png")
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.legend()
        self.fig.savefig(image_path)
        print(f"Graph saved to {image_path}")

        # Save the data as CSV
        csv_filename = os.path.join(self.fileName, f"{self.title}.csv")
        all_keys = list(self.data.keys())
        max_len = max(len(self.data[key][0]) for key in all_keys)

        with open(csv_filename, mode='w', newline='') as csvfile:
            import csv
            writer = csv.writer(csvfile)
            header = []
            for key in all_keys:
                header.extend([f"{key}_x", f"{key}_y"])
            writer.writerow(header)

            for i in range(max_len):
                row = []
                for key in all_keys:
                    x_data, y_data = self.data[key]
                    row.append(x_data[i] if i < len(x_data) else "")
                    row.append(y_data[i] if i < len(y_data) else "")
                writer.writerow(row)

        print(f"CSV data saved to {csv_filename}")

    #Create a new rolling average line
    def add_rolling_average_line(self, name, window=10, colour=None, linestyle="--"):
        """Initialise a rolling average line with internal buffer."""
        self.data[name] = ([], [])
        self.lines[name] = self.ax.plot([], [], label=name, lw=2, linestyle=linestyle, color=colour)[0]
        self.ax.legend()
        if not hasattr(self, 'rolling_buffers'):
            self.rolling_buffers = {}
        self.rolling_buffers[name] = {
            'values': [],
            'window': window
        }


    #Rolling average rate of change
    #Helpful to find the trajectory of adaption
    #Dont really care about magnitude, this is just used to see how fast adaption is taking place
    def add_rolling_derivative(self, source_line_name, new_line_name, window=10, linestyle="--"):
        if source_line_name not in self.data:
            raise ValueError(f"Line '{source_line_name}' does not exist.")
        self.derived_lines[new_line_name] = (source_line_name, window)
        self.data[new_line_name] = ([], [])
        line, = self.ax.plot([], [], label=new_line_name, lw=2, linestyle=linestyle)
        self.lines[new_line_name] = line
        self.ax.legend()

    def push_rolling(self, name, x, y):
        """Push a value to the rolling average line."""
        if name not in self.rolling_buffers:
            raise ValueError(f"Rolling average line '{name}' not initialized. Use add_rolling_average_line().")

        buf = self.rolling_buffers[name]
        buf['values'].append(y)

        if len(buf['values']) > buf['window']:
            buf['values'].pop(0)

        if len(buf['values']) < buf['window']:
            return  # Not enough data yet

        avg = sum(buf['values']) / len(buf['values'])

        x_data, y_data = self.data[name]
        x_data.append(x)
        y_data.append(avg)

        if len(x_data) > self.max_points:
            x_data.pop(0)
            y_data.pop(0)


