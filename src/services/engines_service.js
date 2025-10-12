import axios from 'axios';

export const fetchEngines = () => {
  return new Promise((resolve, reject) => {
    axios.get('/api/v1/engines', {
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

