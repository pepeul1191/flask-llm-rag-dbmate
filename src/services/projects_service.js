import axios from 'axios';

export const fetchProjects = () => {
  return new Promise((resolve, reject) => {
    axios.get('/api/v1/projects', {
      params: {},
      headers:{
        'Client-Origin': 'webapp',
        'Content-Type': 'application/json',
      }
    }).then(function (response) {
      resolve(response.data);
    }).catch(function (error) {
      reject(error.response);
    })
    .then(function () {
      // todo?
    });
  });
}

export const fetchProject = (id) => {
  return new Promise((resolve, reject) => {
    axios.get('/api/v1/projects/' + id, {
      params: {},
      headers:{
        'Client-Origin': 'webapp',
        'Content-Type': 'application/json',
      }
    }).then(function (response) {
      resolve(response.data);
    }).catch(function (error) {
      reject(error.response);
    })
    .then(function () {
      // todo?
    });
  });
}

export const createProject = (engine) => {
  return new Promise((resolve, reject) => {
    axios.post('/api/v1/projects', engine, {
      headers: {
        'Client-Origin': 'webapp',
        'Content-Type': 'application/json',
      }
    }).then(response => {
      resolve(response.data);
    }).catch(error => {
      reject(error.response);
    });
  });
};

export const updateProject = (id, engine) => {
  return new Promise((resolve, reject) => {
    axios.put(`/api/v1/projects/${id}`,engine, {
      headers: {
        'Client-Origin': 'webapp',
        'Content-Type': 'application/json',
      }
    }).then(function (response) {
      resolve(response.data);
    }).catch(function (error) {
      reject(error.response);
    })
    .then(function () {
      // todo?
    });
  });
}

export const deleteProject = (id) => {
  return new Promise((resolve, reject) => {
    axios.delete(`/api/v1/projects/${id}`, {
      headers: {
        'Client-Origin': 'webapp',
        'Content-Type': 'application/json',
      }
    }).then(function (response) {
      resolve(response.data);
    }).catch(function (error) {
      reject(error.response);
    })
    .then(function () {
      // todo?
    });
  });
}

export const createImage = (model) => {
  return new Promise((resolve, reject) => {
    axios.post('/api/v1/image', model, {
      headers: {
        'Client-Origin': 'webapp',
        'Content-Type': 'application/json',
      }
    }).then(response => {
      resolve(response.data);
    }).catch(error => {
      reject(error.response);
    });
  });
};

export const createMigrations = (model, project) => {
  const data = {
    model: model,
    project: project,
  }

  return new Promise((resolve, reject) => {
    axios.post('/api/v1/migrations/generate', data, {
      headers: {
        'Client-Origin': 'webapp',
        'Content-Type': 'application/json',
      }
    }).then(response => {
      resolve(response);
    }).catch(error => {
      reject(error.response);
    });
  });
}