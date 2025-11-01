FROM quay-nonprod.elevancehealth.com/multiarchitecture-golden-base-images/rhel-python-image-with-certs:python-3.12
USER root
WORKDIR /app
COPY ./source/ /app
ENV SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt
ENV CUDA_VISIBLE_DEVICES=""
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/cache/conv_cache
EXPOSE 7860
CMD ["python3", "dsa_app.py"]
 